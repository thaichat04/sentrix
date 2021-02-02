

def initialize_model(conf):
    from transformers import pipeline
    return pipeline('sentiment-analysis')
