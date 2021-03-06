"""
Author: Subho Mukherjee (submukhe@microsoft.com)
Code for XtremeDistil for distilling massive multi-lingual models.
"""

from sklearn.decomposition import PCA
from transformers import *

import logging
import numpy as np
import torch

logger = logging.getLogger('xtremedistil')

# HuggingFace Transformers has a unified API
# for 10 transformer architectures and 30 pretrained weights.
#          Model          | Tokenizer          | Pretrained model config
MODELS = [(BertModel, BertTokenizerFast, BertConfig),
		  (ElectraModel, ElectraTokenizerFast, ElectraConfig),
          (OpenAIGPTModel, OpenAIGPTTokenizerFast, OpenAIGPTConfig),
          (GPT2Model, GPT2TokenizerFast, GPT2Config),
          (CTRLModel, CTRLTokenizer, CTRLConfig),
          (TransfoXLModel,  TransfoXLTokenizer, TransfoXLConfig),
          (XLNetModel, XLNetTokenizer, XLNetConfig),
          (XLMModel, XLMTokenizer, XLMConfig),
          (DistilBertModel, DistilBertTokenizerFast, DistilBertConfig),
          (RobertaModel, RobertaTokenizerFast, RobertaConfig),
          (XLMRobertaModel, XLMRobertaTokenizer, XLMRobertaConfig),
         ]

def get_word_embedding(encoder, pt_tokenizer, hidden_size):
	with torch.no_grad():
	#get word embedding matrix from teacher
		if encoder.base_model_prefix in ['bert','transformer','distilbert','roberta','electra']:
			word_embedding_matrix = encoder.embeddings.word_embeddings.weight.cpu().numpy()
		else:
			logger.info("Base model not supported. Initializing word embedding with random matrix")
			word_embedding_matrix = np.random.uniform(size=(len(pt_tokenizer.get_vocab()), hidden_size))
		logger.info (word_embedding_matrix.shape)
		#embedding factorization to reduce embedding dimension
		if word_embedding_matrix.shape[1] > hidden_size:
			pca =  PCA(n_components = hidden_size)
			word_embedding_matrix = pca.fit_transform(word_embedding_matrix)
			logger.info(" Word embedding matrix compressed to {}".format(word_embedding_matrix.shape))

		return word_embedding_matrix


def get_special_tokens_from_teacher(Tokenizer, pt_tokenizer):

	if hasattr(pt_tokenizer, 'pad_token'):
		pad_token = pt_tokenizer.pad_token
	else:
		pad_token = "<pad>"
	if pt_tokenizer.cls_token is not None and pt_tokenizer.sep_token is not None:
		bos_token = pt_tokenizer.cls_token
		eos_token = pt_tokenizer.sep_token
	else:
		if hasattr(pt_tokenizer, 'bos_token'):
			bos_token = pt_tokenizer.bos_token
		else: 
			bos_token = "<s>"
		if hasattr(pt_tokenizer, 'eos_token'):
			eos_token = pt_tokenizer.eos_token
		else:
			eos_token = "</s>"
	return {"eos_token": eos_token, "bos_token": bos_token, "pad_token": pad_token}

def get_output_state_indices(Model):

	#huggingface pre-trained model output hidden state and attention indices
	if Model == BertModel:
		output_hidden_state_indx = 2
	else:
		output_hidden_state_indx = 1
	output_attention_state_indx = output_hidden_state_indx + 1
	return output_hidden_state_indx, output_attention_state_indx