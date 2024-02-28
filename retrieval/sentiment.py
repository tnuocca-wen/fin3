from transformers import AutoModelForSequenceClassification, AutoTokenizer

def get_model():
    # Specify the model and tokenizer names
    model_name = 'mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis'

    # Load or initialize your model and tokenizer
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # Define the path where you want to save your model
    save_path = "static/sent_model"

    model.save_pretrained(save_path)
    tokenizer.save_pretrained(save_path)