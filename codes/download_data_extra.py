import json
import argparse
import os
import pathlib
import wget

def download_squad(out_dir):
   save_root, local_file = download_data(out_dir, "squad", "https://rajpurkar.github.io/SQuAD-explorer/dataset/train-v1.1.json")   
   with open(local_file) as f:
      data_raw = json.load(f)

   data_out = []
   data_out_id2ans = {}

   data = data_raw['data']
   for d in data:
      for p in d['paragraphs']:
         for q in p['qas']:
               qa_id = q['id']
               answer_text = q['answers'][0]['text']

               data_out_id2ans[qa_id] = [answer_text]
               data_out.append({
                  "id": qa_id,
                  "question": q['question'],
                  "answer": [answer_text]
               })

   out_file = open(os.path.join(save_root, "train.json"), "w")
   json.dump(data_out, out_file)
   out_file.close()

   out_file = open(os.path.join(save_root, "train_id2answers.json"), "w")
   json.dump(data_out_id2ans, out_file)
   out_file.close()

def download_wq(out_dir):
   save_root, local_file = download_data(out_dir, "wq", "https://raw.githubusercontent.com/brmson/dataset-factoid-webquestions/master/main/trainmodel.json")   

   with open(local_file) as f:
      data_raw = json.load(f)

   data_out = []
   data_out_id2ans = {}

   for d in data_raw:
      qa_id = str(ord(d["qId"][0])) + str(ord(d["qId"][1])) + str(ord(d["qId"][2])) + d["qId"][3:]
      answer_text = d['answers']

      data_out_id2ans[qa_id] = d['answers']
      data_out.append({
         "id": qa_id,
         "question": d['qText'],
         "answer": d['answers']
      })

   out_file = open(os.path.join(save_root, "train.json"), "w")
   json.dump(data_out, out_file)
   out_file.close()

   out_file = open(os.path.join(save_root, "train_id2answers.json"), "w")
   json.dump(data_out_id2ans, out_file)
   out_file.close()

def download_data(out_dir, subdir, data_link):
   root_dir = out_dir if out_dir else './'
   save_root = os.path.join(root_dir, subdir)   
   pathlib.Path(save_root).mkdir(parents=True, exist_ok=True)
   print('Loading from ', data_link)
   
   local_file = os.path.join(save_root, "train_data_raw.json")
   if os.path.exists(local_file):
      print('File already exist ', local_file)
      return

   wget.download(data_link, local_file)
   print('\nSaved to', local_file)
   return save_root, local_file

def main():
   parser = argparse.ArgumentParser()

   parser.add_argument("--output_dir", default="./", type=str,
                     help="The output directory to download file")
   parser.add_argument("--resource", type=str,
                     help="Resource name. Either squad (SQuAD dataset) or wq (WebQuestions dataset).")
   args = parser.parse_args()
   if args.resource == "squad":
      download_squad(args.output_dir)
   elif args.resource == "wq":
      download_wq(args.output_dir)
   else:
      print('Please specify resource value. Possible options are: squad (SQuAD dataset) or wq (WebQuestions dataset).')

if __name__ == "__main__":
   main()