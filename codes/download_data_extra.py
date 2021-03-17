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

def download_squad(out_dir,dpr_dir,dpr_data_dir):
   curr_id = 1
   passages = []
   pass_dict = {}
   for split, data_link in SQUAD_RESOURCE_MAP.items():
      save_root, local_file = download_data(out_dir, "squad", split, data_link)
      if not local_file:
         continue
      
      with open(local_file) as f:
         data_raw = json.load(f)

      data_out = []
      data_out_id2ans = {}
      
      data = data_raw['data']
      for d in data:
         for p in d['paragraphs']:
            for q in p['qas']:
               passages.append([curr_id, p["context"], d["title"]])

               pass_dict[q['id']]=(curr_id, p["context"],d["title"])


               curr_id += 1
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
      print(len(data_out))

   print(len(passages))
   print(len(pass_dict))
   if not os.path.exists(os.path.join(dpr_data_dir+"squad/")):
      os.mkdir(os.path.join(dpr_data_dir+"squad"))
   if not os.path.exists(dpr_dir):
      os.mkdir(dpr_data)

   out_file = open(os.path.join(dpr_data_dir,"squad/"+ "passages.json"), "w")
   json.dump(passages,out_file)
   out_file.close()

   out_file = open(os.path.join(save_root, "pass_dict.json"), "w")
   json.dump(pass_dict,out_file)
   out_file.close()

   with open(os.path.join(save_root, "train.json"),"r") as f:
         data= json.load(f)

   split_list=[]
   for d in data:
      split_list.append(d)
   index=int(len(split_list)*0.7)
   train_new = split_list[:index]
   test_new = split_list[index:]
   print(len(train_new))
   print(len(test_new))

   out_file = open(os.path.join(save_root, "train.json"), "w")
   json.dump(train_new,out_file)
   out_file.close()

   out_file = open(os.path.join(save_root, "test.json"), "w")
   json.dump(test_new,out_file)
   out_file.close()

         
   for i in ["train","dev"]:
      with open(os.path.join(save_root, i + ".json"),"r") as f:
         data= json.load(f)

      with open(os.path.join(save_root, "pass_dict.json"),"r") as g:
         passage=json.load(g)

      pred_dpr=[]
      for d in data:
         curr_id,context,title=passage[d['id']]
         pred_dpr.append([curr_id])

      out_file = open(os.path.join(dpr_dir, i + "_predictions.json"), "w")
      json.dump(pred_dpr, out_file)
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
   parser.add_argument("--dpr_dir", default="./out/dpr", type=str,
                     help="The dpr directory to download predictions file")
   parser.add_argument("--dpr_data_dir", default="./dpr_data_dir", type=str,
                     help="The dpr data directory to download passage file")

   parser.add_argument("--resource", type=str,
                     help="Resource name. Either squad (SQuAD dataset) or wq (WebQuestions dataset).")
   args = parser.parse_args()
   if args.resource == "squad":
      download_squad(args.output_dir,args.dpr_dir,args.dpr_data_dir)
   elif args.resource == "wq":
      download_wq(args.output_dir)
   else:
      print('Please specify resource value. Possible options are: squad (SQuAD dataset) or wq (WebQuestions dataset).')

if __name__ == "__main__":
   main()
