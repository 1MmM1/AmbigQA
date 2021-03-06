# AmbigQA Baseline Models (Reproduction)

This repo contains multiple models for open-domain question answering. This code is based on the [original implementation](https://github.com/shmsw25/AmbigQA) and uses [PyTorch][pytorch] and [HuggingFace Transformers][hf].

This repository builds off of the original implementation of "Sewon Min, Julian Michael, Hannaneh Hajishirzi, Luke Zettlemoyer. [AmbigQA: Answering Ambiguous Open-domain Questions][ambigqa-paper]. 2020". Please reference their [repository](https://github.com/shmsw25/AmbigQA) and [website](https://nlp.cs.washington.edu/ambigqa) for more information on the AmbigQA task and AmbigNQ dataset, and make sure to cite their paper if you find them useful.
```
@article{ min2020ambigqa,
    title={ {A}mbig{QA}: Answering Ambiguous Open-domain Questions },
    author={ Min, Sewon and Michael, Julian and Hajishirzi, Hannaneh and Zettlemoyer, Luke },
    journal={ arXiv preprint arXiv:2004.10645 },
    year={2020}
}
```

Please also make sure to credit and cite the creators of Natural Questions, the dataset which AmbigNQ is built off of:
```
@article{ kwiatkowski2019natural,
  title={ Natural questions: a benchmark for question answering research},
  author={ Kwiatkowski, Tom and Palomaki, Jennimaria and Redfield, Olivia and Collins, Michael and Parikh, Ankur and Alberti, Chris and Epstein, Danielle and Polosukhin, Illia and Devlin, Jacob and Lee, Kenton and others },
  journal={ Transactions of the Association for Computational Linguistics },
  year={ 2019 }
}
```

This also contains a re-implementation of "Vladimir Karpukhin*, Barlas Oguz*, Sewon Min, Patrick Lewis, Ledell Wu, Sergey Edunov, Danqi Chen, Wen-tau Yih. [Dense Passage Retrieval for Open-domain Question Answering. 2020][dpr-paper]", as part of AmbigQA models. The original implementation can be found [here][dpr-code]. This codebase achieves higher accuracy.
```
@article{ karpukhin2020dense,
    title={ Dense Passage Retrieval for Open-domain Question Answering },
    author={ Karpukhin, Vladimir and Oguz, Barlas and Min, Sewon and Lewis, Patrick and Wu, Ledell and Edunov, Sergey and Chen, Danqi and Yih, Wen-tau },
    journal={ arXiv preprint arXiv:2004.04906 },
    year={2020}
}
```

## Content
1. [Installation](#installation)
2. [Download data](#download-data)
3. Instructions for Training & Testing
    * [DPR Retrieval](#dpr-retrieval)
    * [DPR Reader (Span Selection Model)](#dpr-reader-span-selection-model)
    * [SpanSeqGen (BART Reader)](#spanseqgen-bart-reader)
    * [Finetuning on AmbigQA](#finetuning-on-ambigqa)
    * [Hyperparameter details / tuning](#hyperparameter-details--tuning)
4. [Results](#results)
    * [Results with less resources](#results-with-less-resources)
5. [Pretrained model checkpoint](#need-preprocessed-data--pretrained-models--predictions)
6. [Usage examples](#usage-examples)
    * [Train only SpanSeqGen](#train-only-spanseqgen)

## Installation
Tested with python 3.6.12 and let $ indicate bash commands.
```
$ pip install torch==1.1.0
$ pip install git+https://github.com/huggingface/transformers.git@7b75aa9fa55bee577e2c7403301ed31103125a35
$ pip install wget
```

## Download data
Let `{dpr_data_dir}` be a directory to save data (can be replaced with a directory of your choosing) and let $ indicate bash commands.
```
$ mkdir {dpr_data_dir}
$ python3 download_data.py --resource data.wikipedia_split.psgs_w100 --output_dir {dpr_data_dir}
$ python3 download_data.py --resource data.wikipedia_split.psgs_w100_20200201 --output_dir {dpr_data_dir}
$ python3 download_data.py --resource data.nqopen --output_dir data
# python3 download_data.py --resource data.gold_passages_info.nq_train --output_dir data
# python3 download_data.py --resource data.ambigqa --output_dir data
```

## DPR Retrieval
For training DPR retrieval, please refer to the [original implementation][dpr-code]. This code is for taking checkpoint from the original implementation, and running inference. 

Step 1: Download DPR retrieval checkpoint provided by DPR original implementation.
```
$ python3 download_data.py --resource checkpoint.retriever.multiset.bert-base-encoder --output_dir {dpr_data_dir}
```

Step 2: Run inference to obtain passage vectors. Note: if you are using a checkpoint, there is no need to run this section, and you may skip to [DPR Reader (Span Selection Model)](#dpr-reader-span-selection-model).
```
$ for i in 0 1 2 3 4 5 6 7 8 9 ; do \ # for parallelization
    python3 cli.py --do_predict --bert_name bert-base-uncased --output_dir out/dpr --dpr_data_dir dpr_data_dir --do_predict --task dpr --predict_batch_size 3200 --db_index $i ; \
    done
```
- `--predict_batch_size` of 3200 is good for one 32gb GPU.
- `--verbose` to print a progress bar
- This script will tokenize passages in Wikipedia which will takes time. If you want to pre-tokenize first and then launch the job on gpus afterward, please do the following: (1) run the above command with `--do_prepro_only`, and (2) re-run the above command without `--do_prepro_only`.

Each run will take around 1.5 hours with one 32 gpu.

Step 3: Run inference to obtain question vectors and save the retrieval predictions.
```
python3 cli.py --bert_name ber-base-uncased --output_dir out/dpr --dpr_data_dir data --do_predict --task dpr --predict_batch_size 3200 --predict_file data/nqopen/{train|dev|test}.json
```

This script will print out recall rate and save the retrieval results as `out/dpr/{train|dev|test}_predictions.json`.

Tip1: Running this for the first time regardless of the data split will create DPR index and save it, so that the next runs can reuse them. If you do not want to create DPR index multiple times, you can run on one data split first, and run the others afterward. If you have resource to run them in parallel, it may save time to just run all of them in parallel.

Tip2: If you are fine with not printing the recall rate, you can specify `--skip_db_load` to save time. It will then print the recall to be 0, but the prediction file will be saved with no problem.

## DPR Reader (Span Selection Model)

Note: if you are using a checkpoint, there is no need to run this section, and you may skip to [SpanSeqGen (BART Reader)](#spanseqgen-bart-reader).

For training on NQ-open, run
```
$ python3 cli.py --do_train --task qa --output_dir out/nq-span-selection \
    --dpr_data_dir {dpr_data_dir} \
    --train_file data/nqopen/train.json \
    --predict_file data/nqopen/dev.json \
    --bert_name {bert-base-uncased|bert-large-uncased} \
    --train_batch_size 32 --train_M 32 --predict_batch_size 128 \
    --eval_period 2000 --wait_step 10
```

- This script will save preprocessed input data so that it can re-load them once it is created. You might want to preprocess data before launching a job on GPUs.
- `train_batch_size` is # of questions / batch, and `train_M` is # of passages / question. Thus, # of (question, passage) / batch is `train_batch_size * train_M`, which matters for GPU usage. With one 32gb GPU and bert-base-uncased, you can use `train_batch_size * train_M` of 128, as hyperparamters specified in the command above.
- `eval_period` is an interval to test on the dev data. The script will only save the best checkpoint based on the dev data. If you prefer, you can specify `skip_inference` to skip inference on the dev data and save all checkpoints. You can then run the inference script (described next) on the dev data using every checkpoint, and choose the best checkpoint.
- `wait_step` is the number of steps to wait since the best checkpoint, until the training is finished.

When training is done, run the following command for prediction.
```
$ python3 cli.py --do_predict --task qa --output_dir out/nq-span-selection \
    --dpr_data_dir {dpr_data_dir} \
    --predict_file data/nqopen/{dev|test}.json \
    --bert_name {bert-base-uncased|bert-large-uncased} \
    --predict_batch_size 32
```
This command runs predictions using `out/nq-span-selection/best-model.pt` by default. If you want to run predictions using another checkpoint, please specify its path by `--checkpoint`.


## SpanSeqGen (BART Reader)

You may train the SpanSeqGen model on NQ-open (as done in the original paper) or on SQuAD (new in our reproduction). Note that this model is different from BART closed-book QA model (implemented [here][bart-closed-book-qa]), because this model reads DPR retrieved passages as input.

### Train on NQ-open

Note: if you are using a checkpoint, there is no need to run the first two code segments since the passages have already been selected. You may simply run the third code segment (though please make sure that the checkpoint is located in `out/nq-span-selection`).

First, tokenize passage vectors.
```
$ for i in 0 1 2 3 4 5 6 7 8 9 ; do \ # for parallelization
    python3 cli.py --bert_name bart-large --output_dir out/dpr --dpr_data_dir {dpr_data_dir} --do_predict --do_prepro_only --task dpr --predict_batch_size 3200 --db_index $i \
    done
```

Then, save passage selection from the trained DPR reader:
```
$ python3 cli.py --do_predict --task qa --output_dir out/nq-span-selection \
    --dpr_data_dir {dpr_data_dir} \
    --predict_file data/nqopen/{train|dev|test}.json \
    --bert_name {bert-base-uncased|bert-large-uncased} \
    --predict_batch_size 32 --save_psg_sel_only
```

Now, train a model on NQ-open by:
```
$ python3 cli.py --do_train --task qa --output_dir out/nq-span-seq-gen \
    --dpr_data_dir {dpr_data_dir} \
    --train_file data/nqopen/train.json \
    --predict_file data/nqopen/dev.json \  
    --psg_sel_dir out/nq-span-selection \   
    --bert_name bart-large \
    --discard_not_found_answers \
    --train_batch_size 2 --predict_batch_size 2 \
    --eval_period 2000 --wait_step 10 --max_input_length 700
```
* `--max_input_length` is the maximum length of the input. Any input longer than this number will be truncated. The original authors used 1024 for this value but we suggest using 700 if you are using a smaller GPU (e.g. 12 GB).

* `--do_train` specifies that we are training the model. If you would like to evaluate your model on NQ-open, you may do so by replacing this command line argument with `--do_predict` as shown in the box below
```
$ python3 cli.py --do_predict --task qa --output_dir out/nq-span-seq-gen \
    --dpr_data_dir {dpr_data_dir} \
    --train_file data/nqopen/train.json \
    --predict_file data/nqopen/dev.json \
    --psg_sel_dir out/nq-span-selection \
    --bert_name bart-large \
    --discard_not_found_answers \
    --train_batch_size 2 --predict_batch_size 2 \
    --eval_period 2000 --wait_step 10 --max_input_length 700
```

### Train on SQuAD
First, we must preprocess the dataset to be the correct format
``` 
$ python3 download_data_extra.py --output_dir data/ \
    --dpr_data_dir {dpr_data_dir} \
    --dpr_dir out/dpr/
    -- resouce squad
```

Now you may train a model on SQuAD:
```
$ python3 cli.py --do_train --task qa --output_dir out/squad-span-seq-gen     
    --dpr_data_dir {dpr_data_dir} \
    --train_file data/squad/train.json \
    --predict_file data/squad/dev.json \
    --psg_sel_dir out/nq-span-selection \
    --bert_name bart-large \
    --discard_not_found_answers \
    --train_batch_size 2   
    --predict_batch_size 2 \
    --eval_period 2000 --wait_step 10 --train_on_squad --max_input_length 150
```
To evaluate your model on SQuAD, replace the `--do_train` command line argument with `--do_predict` as shown in the box below
```
$ python3 cli.py --do_predict --task qa --output_dir out/squad-span-seq-gen \
    --dpr_data_dir {dpr_data_dir} \
    --train_file data/squad/train.json \
    --predict_file data/squad/dev.json \
    --psg_sel_dir out/nq-span-selection \
    --bert_name bart-large \
    --discard_not_found_answers \
    --train_batch_size 2 --predict_batch_size 2 \
    --eval_period 2000 --wait_step 10 --train_on_squad --max_input_length 150
```

## Finetuning on AmbigQA

In order to experiment on AmbigQA, you can simply repeat the process with NQ-open, with only two differences - (i) specifying `--ambigqa` and `--wiki_2020` at several places and (ii) initialize weights from models trained on NQ-open. Step-by-step instructions are as follows.

First, make DPR retrieval predictions using Wikipedia 2020. You can do so by simply repeating Step 2 and Step 3 of [DPR Retrieval](#dpr-retrieval) with `--wiki_2020` specified. 

Note: if you are using a checkpoint, there is no need to run the next three code segments. You may skip directly to the fourth code segment to fine tune on AmbigNQ.
```
$ for i in 0 1 2 3 4 5 6 7 8 9 ; do \ # for parallelization
    python3 cli.py --do_predict --bert_name bert-base-uncased --output_dir out/dpr --dpr_data_dir {dpr_data_dir} --do_predict --task dpr --predict_batch_size 3200 --db_index $i --wiki_2020 \
    done
$ python3 cli.py --do_predict --task dpr --output_dir out/dpr \
    --dpr_data_dir {dpr_data_dir} \
    --predict_file data/nqopen/{train|dev|test}.json \
    --bert_name ber-base-uncased \
    --predict_batch_size 3200  --wiki_2020
```

In order to fine-tune DPR span selection model on AmbigQA, run the training command similar to NQ training command, but with `--ambigqa` and `--wiki2020` specified. We also used smaller `eval_period` as the dataset size is smaller.
```
$ python3 cli.py --do_train --task qa --output_dir out/ambignq-span-selection \
    --dpr_data_dir {dpr_data_dir} \
    --train_file data/ambigqa/train_light.json \
    --predict_file data/ambigqa/dev_light.json \
    --bert_name {bert-base-uncased|bert-large-uncased} \
    --train_batch_size 32 --train_M 32 --predict_batch_size 32 \
    --eval_period 500 --wait_step 10 --topk_answer 3 --ambigqa --wiki_2020
```

In order to fine-tune SpanSeqGen on AmbigQA, first run the inference script over DPR to get highly ranked passages, just like we did on NQ.
```
$ python3 cli.py --do_predict --task qa --output_dir out/nq-span-selection \
    --dpr_data_dir {dpr_data_dir} \
    --predict_file data/nqopen/{train|dev|test}.json \
    --bert_name {bert-base-uncased|bert-large-uncased} \
    --predict_batch_size 32 --save_psg_sel_only --wiki_2020
```

Next, train SpanSeqGen on AmbigNQ via the following command, which specifies `--ambigqa`, `--wiki_2020` and `--max_answer_length 25`.
```
$ python3 cli.py --do_train --task qa --output_dir out/ambignq-span-seq-gen \
    --dpr_data_dir {dpr_data_dir} \
    --train_file data/ambigqa/train_light.json \
    --predict_file data/ambigqa/dev_light.json \
    --psg_sel_dir out/nq-span-selection \
    --bert_name bart-large \
    --discard_not_found_answers \
    --train_batch_size 2 --predict_batch_size 2 \
    --eval_period 500 --wait_step 10 --ambigqa --wiki_2020 \
    --max_answer_length 25 --max_input_length 700
```
To evaluate your model on AmbigNQ, simply replace `--do_train` in the previous command with `--do_predict` as shown below:
```
$ python3 cli.py --do_predict --task qa --output_dir out/ambignq-span-seq-gen \
    --dpr_data_dir {dpr_data_dir} \
    --train_file data/ambigqa/train_light.json \
    --predict_file data/ambigqa/dev_light.json \
    --psg_sel_dir out/nq-span-selection \
    --bert_name bart-large \
    --discard_not_found_answers \
    --train_batch_size 2 --predict_batch_size 2 \
    --eval_period 500 --wait_step 10 --ambigqa --wiki_2020 \
    --max_answer_length 25 --max_input_length 700
```

## Hyperparameter details / tuning

**On NQ-open:** For BERT-base, we use `train_batch_size=32, train_M=32` (w/ eight 32GB gpus). For BERT-large, we use `train_batch_size=8, train_M=16` (w/ four 32GB gpus). For BART, we use `train_batch_size=24` (w/ four 32GB gpus). For others, we use default hyperparameters.

**On AmbigQA:** We use `train_batch_size=8` for BERT-base and `train_batch_size=24` for BART. We use `learning_rate=5e-6` for both.

To do the exploration of hyperparameter impact on beam size or the inference time, simply run the included bash script as shown below. This will try several values for beam size (1, 2, 6, 10, and 12), length penalty (1, 3, 5, and 10), and no repeat ngram (0, 1, 2, 3). To try different values, please edit the `beams`, `penaltys`, and `ngrams` variables in `run_inference_hyper.sh`.
```
$ ./run_inference_hyper.sh
```

## Results

|   | NQ-open (dev) | NQ-open (test) | AmbigQA zero-shot (dev) | AmbigQA zero-shot (test) | AmbigQA (dev) | AmbigQA (test) |
|---|---|---|---|---|---|---|
|DPR (original implementation)| 39.8 | 41.5 | 35.2/26.5 | 30.1/23.2 | 37.1/28.4 | 32.3/24.8 |
|DPR (this code)| 40.6 | 41.6 | 35.2/23.9 | 29.9/21.4 | 36.8/25.8 | 33.3/23.4 |
|DPR (this code) w/ BERT-large| 43.2 | 44.3 | - | - | - | - |
|SpanSeqGen (reported)| 42.0 | 42.2 | 36.4/24.8 | 30.8/20.7 | 39.7/29.3 | 33.5/24.5 |
|SpanSeqGen (this code)| 43.1 | 45.0 | 37.4/26.1 | 33.2/22.6 | 40.3/29.2 | 35.5/25.8 |

Two numbers on AmbigQA indicate F1 score on all questions and F1 score on questions with multiple QA pairs only.

By default, the models are based on BERT-base and BART-large.

*Note (as of 07/2020)*: Note that numbers are slightly different from those reported in the paper, because numbers in the paper are based on experiments with fairseq. We re-implemented the models with Huggingface Transformers, and were able to obtain similar/better numbers. We will update numbers in the paper of the next version.

*Note*: There happen to be two versions of NQ answers which marginally differ in tokenization methods (e.g. `July 15 , 2020` vs. `July 15, 2020` or `2019 - 2020` vs. `2019--2020`).
Research papers outside Google ([#1][dpr-paper], [#2][ambigqa-paper], [#3][hard-em], [#4][path-retriever], [#5][rag], [#6][colbert], [#7][fusion-decoder], [#8][graph-retriever]) have been using [this version](https://nlp.cs.washington.edu/ambigqa/data/nqopen.zip), and in June 2020 the original NQ/NQ-open authors release the [original version](https://github.com/efficientqa/nq-open) that have been used in research papers from Google ([#1][orqa], [#2][realm], [#3][t5qa]).
We verified that the performance differences are marginal when applying simple postprocessing (e.g. `text.replace(" - ", "-").replace(" : ", ":")`).
The numbers reported here as well as codes follow Google's original version. Compared to the previous version, performance difference is 40.6 (original) vs. 40.3 (previous) vs. 40.7 (union of two) on the dev set and 41.6 (original) vs. 41.7 (previous) vs. 41.8 (union of two) on the test set.
Nonetheless, we advice to use the original version provided by Google in the future.

### Results with less resources

The readers are not very sensitive to hyperparamters (`train_batch_size` and `train_M`). In case you want to experiment with less resources and want to check the reproducibility, here are our results depending on the number of 32gb GPUs.

DPR with BERT-base:
| Num. of 32gb GPU(s) | (`train_batch_size`, `train_M`) | NQ-open (dev) | NQ-open (test) |
|---|---|---|---|
| 1 | (8, 16) | 40.5 | 41.4 |
| 2 | (16, 16) | 40.9 | 41.1 |
| 4 | (16, 32) | 41.2 | 41.1 |
| 8 | (32, 32) | 40.6 | 41.6 |

DPR with BERT-large:
| Num. of 32gb GPU(s) | (`train_batch_size`, `train_M`) | NQ-open (dev) | NQ-open (test) |
|---|---|---|---|
| 2 | (8, 8) | 42.0 | 43.4 |
| 4 | (8, 16) | 43.2 | 44.3 |
| 8 | (16, 16) | 42.2 | 43.2 |

SpanSeqGen with BART-large:
| Num. of 12GB GPU(s) | (`train_batch_size`, `max_input_len`) | NQ-open EM (dev) | AmbigNQ F1 (dev) |
|---|---|---|---|
| 1 | (2, 700) | 37.81 | 39.38 | 

## Need preprocessed data / pretrained models / predictions?

**DPR**
- [DPR predictions on NQ](https://nlp.cs.washington.edu/ambigqa/models/nq-dpr.zip)

**Question Answering**
Click in order to download checkpoints:
- [DPR Reader trained on NQ (387M)][checkpoint-nq-dpr]
- [DPR Reader (w/ BERT-large) trained on NQ (1.2G)][checkpoint-nq-dpr-large]
- [DPR Reader trained on AmbigNQ (387M)][checkpoint-ambignq-dpr]
- [SpanSeqGen trained on NQ (1.8G)][checkpoint-nq-bart]
- [SpanSeqGen trained on AmbigNQ (1.8G)][checkpoint-ambignq-bart]

**Passage Reranking from DPR Reader**
- [Reranking result (37M)](https://nlp.cs.washington.edu/ambigqa/models/reranking_results.zip): contain reranking for NQ train/dev/test (aligned with [Wikipedia 2018](https://github.com/shmsw25/AmbigQA/blob/master/codes/download_data.py#L26) and AmbigQA train/dev (aligned with [Wikipedia 2020](https://github.com/shmsw25/AmbigQA/blob/master/codes/download_data.py#L34)).

For a sanity check, the recall accuracy should be as follows. (For AmbigQA, macro-average of recall.)

| k | NQ train | NQ dev | NQ test | AmbigQA train | AmbigQA dev |
|---|---|---|---|---|---|
| 1     |80.4|59.8|59.4|58.3|51.8|
| 5     |86.8|75.9|76.3|72.7|70.0|
| 10    |87.8|79.9|80.8|76.2|74.8|
| 100   |89.2|86.2|87.4|81.2|83.1|

**Question Disambiguation**
Coming soon!

[ambigqa-paper]: https://arxiv.org/abs/2004.10645
[dpr-paper]: https://arxiv.org/abs/2004.04906
[dpr-code]: https://github.com/facebookresearch/DPR
[bart-closed-book-qa]: https://github.com/shmsw25/bart-closed-book-qa
[hf]: https://huggingface.co/transformers/
[pytorch]: https://pytorch.org/

[hard-em]: https://arxiv.org/abs/1909.04849
[path-retriever]: https://arxiv.org/abs/1911.10470
[rag]: https://arxiv.org/abs/2005.11401
[fusion-decoder]: https://arxiv.org/abs/2007.01282
[colbert]: https://arxiv.org/abs/2007.00814
[graph-retriever]: https://arxiv.org/abs/1911.03868

[orqa]: https://arxiv.org/abs/1906.00300
[realm]: https://arxiv.org/abs/2002.08909
[t5qa]: https://arxiv.org/abs/2002.08910

[checkpoint-nq-dpr]: https://nlp.cs.washington.edu/ambigqa/models/nq-bert-base-uncased-32-32-0.zip
[checkpoint-nq-dpr-large]: https://nlp.cs.washington.edu/ambigqa/models/nq-bert-large-uncased-16-16-0.zip
[checkpoint-ambignq-dpr]: https://nlp.cs.washington.edu/ambigqa/models/ambignq-bert-base-uncased-8-32-0.zip
[checkpoint-nq-bart]: https://nlp.cs.washington.edu/ambigqa/models/nq-bart-large-24-0.zip
[checkpoint-ambignq-bart]: https://nlp.cs.washington.edu/ambigqa/models/ambignq-bart-large-12-0.zip

## Usage examples

Here are some examples for running these models:

### Train only SpanSeqGen

In the below run we use checkpoints for DPR Retrieval and DPR Reader to train SpanSeqGen on NQ-open, then fine tune the trained model on AmbigQA. This run has been successfully tested by running on a single Azure NC12 machine (24 GiB).

```
$ conda create --name ambigqa python=3.6.12
$ conda activate ambigqa

# Import libraries
$ pip install torch==1.1.0
$ pip install git+https://github.com/huggingface/transformers.git@7b75aa9fa55bee577e2c7403301ed31103125a35
$ pip install wget

# Clone git repository
$ git clone https://github.com/1MmM1/AmbigQA.git
$ cd AmbigQA/codes

# Download data
$ mkdir dpr_data_dir
$ python3 download_data.py --resource data.wikipedia_split.psgs_w100 --output_dir ./dpr_data_dir
$ python3 download_data.py --resource data.wikipedia_split.psgs_w100_20200201 --output_dir ./dpr_data_dir
$ python3 download_data.py --resource checkpoint.retriever.multiset.bert-base-encoder --output_dir ./dpr_data_dir
$ python3 download_data.py --resource data.nqopen --output_dir ./data
$ python3 download_data.py --resource data.gold_passages_info.nq_train --output_dir ./data
$ python3 download_data.py --resource data.ambigqa --output_dir ./data

# Download checkpoint for DPR predictions on NQ
$ mkdir out
$ mkdir out/dpr
$ wget https://nlp.cs.washington.edu/ambigqa/models/nq-dpr.zip
$ unzip nq-dpr.zip
$ mv nq-dpr/* out/dpr/
$ rm -r nq-dpr

# Download Reranking result (37M)
$ mkdir out/nq-span-selection
$ wget https://nlp.cs.washington.edu/ambigqa/models/reranking_results.zip
$ unzip reranking_results.zip
$ mv reranking_results/nq_dev.json out/nq-span-selection/dev_psg_sel.json
$ mv reranking_results/nq_train.json out/nq-span-selection/train_for_inference_psg_sel.json
$ mv reranking_results/nq_test.json out/nq-span-selection/test_psg_sel.json

# Download DPR Reader trained on NQ (387M)
$ wget https://nlp.cs.washington.edu/ambigqa/models/nq-bert-base-uncased-32-32-0.zip
$ unzip nq-bert-base-uncased-32-32-0.zip
$ mv nq-bert-base-uncased-32-32-0/best-model.pt out/nq-span-selection/
$ rm -r nq-bert-base-uncased-32-32-0

$ rm *.zip

# Train SpanSeqGen
$ conda activate ambigqa
$ python3 cli.py --do_train --task qa --output_dir out/nq-span-seq-gen \
    --dpr_data_dir ./dpr_data_dir \
    --train_file ./data/nqopen/train.json \
    --predict_file ./data/nqopen/dev.json \
    --psg_sel_dir ./out/nq-span-selection \
    --bert_name bart-large \
    --discard_not_found_answers \
    --train_batch_size 2 --predict_batch_size 2 \
    --eval_period 2000 --wait_step 10 --max_input_length 700

# Fine tune on AmbigQA
$ mv reranking_results/ambigqa_dev_2020.json out/nq-span-selection/dev_20200201_psg_sel.json
$ mv reranking_results/ambigqa_train_2020.json out/nq-span-selection/train_for_inference_20200201_psg_sel.json
$ python3 cli.py --do_train --task qa --output_dir out/ambignq-span-seq-gen \
    --dpr_data_dir dpr_data_dir \
    --train_file data/ambigqa/train_light.json \
    --predict_file data/ambigqa/dev_light.json \
    --psg_sel_dir out/nq-span-selection \
    --bert_name bart-large \
    --discard_not_found_answers \
    --train_batch_size 2 --predict_batch_size 2 \
    --eval_period 500 --wait_step 10 --ambigqa --wiki_2020 --max_answer_length 25

# Do hyperparameter impact on inference time
$ ./run_inference_hyper.sh
```

