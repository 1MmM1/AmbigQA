import json
import argparse
import os
import pathlib
import wget

SQUAD_RESOURCE_MAP = {
   "train": "https://rajpurkar.github.io/SQuAD-explorer/dataset/train-v1.1.json",
   "dev": "https://rajpurkar.github.io/SQuAD-explorer/dataset/dev-v1.1.json"
}

WQ_RESOURCE_MAP = {
   "train": "https://raw.githubusercontent.com/brmson/dataset-factoid-webquestions/master/main/trainmodel.json",
   "dev": "https://raw.githubusercontent.com/brmson/dataset-factoid-webquestions/master/main/val.json",
   "test": "https://raw.githubusercontent.com/brmson/dataset-factoid-webquestions/master/main/test.json"
}

def download_squad(out_dir):
   curr_id = 1
   for split, data_link in SQUAD_RESOURCE_MAP.items():
      save_root, local_file = download_data(out_dir, "squad", split, data_link)
      if not local_file:
         continue
      
      with open(local_file) as f:
         data_raw = json.load(f)

      data_out = []
      data_out_id2ans = {}
      passages = []

      data = data_raw['data']
      for d in data:
         for p in d['paragraphs']:
            passages.append([curr_id, p["context"], d["title"]])
            curr_id += 1
            for q in p['qas']:
                  qa_id = q['id']
                  answers =[answer['text'] for answer in q['answers']]

                  data_out_id2ans[qa_id] = answers
                  data_out.append({
                     "id": qa_id,
                     "question": q['question'],
                     "answer": answers
                  })

      out_file = open(os.path.join(save_root, split + ".json"), "w")
      json.dump(data_out, out_file)
      out_file.close()

      out_file = open(os.path.join(save_root, split + "_id2answers.json"), "w")
      json.dump(data_out_id2ans, out_file)
      out_file.close()

      out_file = open(os.path.join(save_root, split + "_passages.json"), "w")
      for passage in passages:
         out_file.write(str(passage[0]) + "\t" + passage[1] + "\t" + passage[2] + "\n")
      out_file.close()

def download_wq(out_dir):
   for split, data_link in WQ_RESOURCE_MAP.items():
      save_root, local_file = download_data(out_dir, "wq", split, data_link)
      if not local_file:
         continue

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

      out_file = open(os.path.join(save_root, split + ".json"), "w")
      json.dump(data_out, out_file)
      out_file.close()

      out_file = open(os.path.join(save_root, split + "_id2answers.json"), "w")
      json.dump(data_out_id2ans, out_file)
      out_file.close()

def download_data(out_dir, subdir, split, data_link):
   root_dir = out_dir if out_dir else './'
   save_root = os.path.join(root_dir, subdir)   
   pathlib.Path(save_root).mkdir(parents=True, exist_ok=True)
   print('Loading from ', data_link)
   
   local_file = os.path.join(save_root, split + "_data_raw.json")
   if os.path.exists(local_file):
      print('File already exists: ', local_file)
      local_file = None
   else:
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