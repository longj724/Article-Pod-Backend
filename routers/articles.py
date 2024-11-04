from pydantic import BaseModel
from typing import List
from fastapi import APIRouter, HTTPException
from newspaper import Article as NewsArticle
from newspaper.article import ArticleException
from google.cloud import texttospeech
from google.oauth2 import service_account
import os
import tempfile
from uuid import uuid4, UUID
from fastapi.responses import Response

from api.models import Article
from api.deps import db_dependency
from api.services.s3_service import S3Service

credentials = service_account.Credentials.from_service_account_file(
    'article-pod-service-account.json'
)

class ArticleCreate(BaseModel):
    url: str
    textToSpeechModel: str

class ArticleResponse(BaseModel):
    id: UUID
    title: str
    content: str | None
    content_url: str | None
    audio_url: str
    speech_model: str

class TestVoiceRequest(BaseModel):
    voice: str
    text: str

router = APIRouter(
    prefix='/articles',
    tags=['articles']
)

@router.get("/", response_model=List[ArticleResponse])
async def get_articles(db: db_dependency):
    articles = db.query(Article).all()
    print(articles)
    return articles

@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: str, db: db_dependency):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@router.post("/", response_model=ArticleResponse, status_code=201)
async def create_article(article: ArticleCreate, db: db_dependency):
    try:
        news_article = NewsArticle(article.url)
        news_article.download()
        news_article.parse()
        
        # Check if we got the essential information
        if not news_article.title or not news_article.text:
            raise HTTPException(
                status_code=422,
                detail="Could not extract article content from the provided URL"
            )
        
        # Initialize Text-to-Speech client
        tts_client = texttospeech.TextToSpeechClient(credentials=credentials)
        
        # Configure audio
        synthesis_input = texttospeech.SynthesisInput(text=news_article.text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name=article.textToSpeechModel,
            ssml_gender=texttospeech.SsmlVoiceGender.MALE
        )

        print(f"Using voice: {voice}")

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        # Perform text-to-speech
        response = tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        audio_filename = f"article_audio_{uuid4()}-{news_article.title}.mp3"

        
        # Save the audio file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio_file:
            temp_audio_file.write(response.audio_content)
            temp_audio_path = temp_audio_file.name
            
        print(f"Audio filename: {audio_filename}")

        s3_service = S3Service()
        audio_url = s3_service.upload_file(temp_audio_path, audio_filename)
        os.unlink(temp_audio_path)

        db_article = Article(
            title=news_article.title,
            content=news_article.text,
            content_url=article.url,
            audio_url=audio_url,
            speech_model=article.textToSpeechModel
        )
        
        db.add(db_article)
        db.commit()
        db.refresh(db_article)
        return db_article
        
    except ArticleException as e:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to parse article: {str(e)}"
        )
    except Exception as e:
        print(f"{str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the article: {str(e)}"
        )

@router.delete("/{article_id}")
async def delete_article(article_id: str, db: db_dependency):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    db.delete(article)
    db.commit()
    return article

@router.post("/test-voice")
async def test_voice(request: TestVoiceRequest):
    try:
        client = texttospeech.TextToSpeechClient(credentials=credentials)

        synthesis_input = texttospeech.SynthesisInput(text=request.text)

        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name=request.voice
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        
        return Response(
            content=response.audio_content,
            media_type="audio/mpeg"
        )
    except Exception as e:
        return Response(
            status_code=500,
            content=str(e)
        )

