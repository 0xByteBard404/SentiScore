from torch import nn
from transformers import BertForSequenceClassification


class SentimentClassifier(nn.Module):
    def __init__(self, num_classes=1):
        super(SentimentClassifier, self).__init__()
        self.bert = BertForSequenceClassification.from_pretrained(
            'bert-base-chinese', num_labels=num_classes)

    def forward(self, input_ids, attention_mask, token_type_ids):
        outputs = self.bert(
            input_ids=input_ids, attention_mask=attention_mask, token_type_ids=token_type_ids)
        return outputs[0]


def load_model(model, path, device):
    """加载模型权重"""
    import torch
    model.load_state_dict(torch.load(path, map_location=device), strict=False)
    return model