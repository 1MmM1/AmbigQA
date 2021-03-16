#!/bin/bash

beams="1 2 6 10 12"

for beam in ${beams}; do    
    python3 cli.py \
	--do_predict \
	--task qa \
	--output_dir out/nq-span-seq-gen \
	--dpr_data_dir  dpr_data_dir/ \
	--train_file  data/nqopen/train.json \
	--predict_file  data/nqopen/test.json \
	--psg_sel_dir  out/nq-span-selection \
	--bert_name bart-large \
	--discard_not_found_answers \
	--train_batch_size 2 \
	--predict_batch_size 2 \
	--eval_period 2000 \
	--wait_step 10 \
	--num_beams ${beam}
done > hyper_output.txt

penaltys="1 3 5 10"

for penalty in ${penaltys}; do
    python3 cli.py \
	--do_predict \
	--task qa \
	--output_dir out/nq-span-seq-gen \
	--dpr_data_dir  dpr_data_dir/ \
	--train_file  data/nqopen/train.json \
	--predict_file  data/nqopen/test.json \
	--psg_sel_dir  out/nq-span-selection \
	--bert_name bart-large \
	--discard_not_found_answers \
	--train_batch_size 2 \
	--predict_batch_size 2 \
	--eval_period 2000 \
	--wait_step 10 \
	--length_penalty ${penalty}
done > penalty_output.txt

ngrams="0 1 2 3"
echo ${ngrams}

for ngram in ${ngrams}; do
    python3 cli.py \
	--do_predict \
	--task qa \
	--output_dir out/nq-span-seq-gen \
	--dpr_data_dir  dpr_data_dir/ \
	--train_file  data/nqopen/train.json \
	--predict_file  data/nqopen/test.json \
	--psg_sel_dir  out/nq-span-selection \
	--bert_name bart-large \
	--discard_not_found_answers \
	--train_batch_size 2 \
	--predict_batch_size 2 \
	--eval_period 2000 \
	--wait_step 10 \
	--no_repeat_ngram_size ${ngram}
done > ngram_output.txt


