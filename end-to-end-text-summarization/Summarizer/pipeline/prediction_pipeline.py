import os, sys
import torch
from Summarizer.logger import logging
import re


from Summarizer.entity.config_entity import PredictionPipelineConfig
from Summarizer.exception import CustomException
from Summarizer.components.model_finetuner import T5smallFinetuner
from Summarizer.constant import *
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

model_path= r"C:\Users\shiva\Desktop\Text_Summarization\Saved_model\model.pt"


class SinglePrediction:
    def __init__(self):
        try: 
            self.prediction_config = PredictionPipelineConfig()
            base_model_name = self.prediction_config.base_model_name
            
            self.base_model = AutoModelForSeq2SeqLM.from_pretrained(base_model_name)
            
            self.tokenizer = AutoTokenizer.from_pretrained(base_model_name)
        except Exception as e:
            raise CustomException(e, sys)
    
    def summarize_text(self, text, model):
        whitespace_handler = lambda k: re.sub('\s+', ' ', re.sub('\n+', ' ', k.strip()))
        text_encoding = self.tokenizer(
            whitespace_handler(text),
            max_length=self.prediction_config.input_max_length,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt'
        )
        generated_ids = model.model.generate(
            input_ids=text_encoding['input_ids'],
            attention_mask=text_encoding['attention_mask'],
            max_length=self.prediction_config.output_max_length,
            num_beams=self.prediction_config.num_beams,
            no_repeat_ngram_size=2,
            length_penalty=1.0,
            early_stopping=True
        )
        preds = [self.tokenizer.decode(gen_id, skip_special_tokens=True, clean_up_tokenization_spaces=False)for gen_id in generated_ids]
        return "".join(preds)



    def prediction_step(self, input_text, model):
        try: 
            with torch.no_grad():
                summary = self.summarize_text(text = input_text, model=model)
                logging.info("Summary of the input text: {}".format(summary))
                return summary
        except Exception as e:
            raise CustomException(e, sys)
    
    def get_model(self):
        try: 
            prediction_model_path = model_path
            
            logging.info(f" Accessing model : {prediction_model_path}")
            
            if prediction_model_path is None:
                return None
            else:
                prediction_model = T5smallFinetuner(model=self.base_model, tokenizer=self.tokenizer)
                model_state_dict = torch.load(prediction_model_path, map_location='cpu')
                prediction_model.load_state_dict(model_state_dict['model_state_dict'])
                prediction_model.eval()
            return prediction_model
        except Exception as e:
            raise CustomException(e, sys)
    
    def predict(self, input_text):
        try:
            prediction_model = self.get_model()
            generated_predictions =  self.prediction_step(input_text=input_text, 
                                                         model=prediction_model)
            return generated_predictions
        except Exception as e:
            raise CustomException(e, sys)