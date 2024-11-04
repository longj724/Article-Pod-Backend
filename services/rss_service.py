from datetime import datetime, timezone
from feedgen.feed import FeedGenerator
import tempfile
from api.services.s3_service import S3Service
from api.models import Article

class RSSService:
    def __init__(self):
        self.s3_service = S3Service()
        self.feed_filename = "podcast_feed.xml"
        
    def _create_feed(self):
        fg = FeedGenerator()
        fg.load_extension('podcast')
        
        fg.title('ArticlePod Feed')
        fg.description('Audio versions of your favorite articles')
        fg.link(href='https://longj724.github.io/')  # Replace with your actual website
        fg.language('en')
        fg.author({'name': 'ArticlePod'})
        # fg.logo('https://your-website.com/logo.png')  # Replace with your actual logo URL
        fg.podcast.itunes_category('Technology')

        print('fg is', fg)
        
        return fg
    
    def _get_existing_feed(self):
        try:
            feed_content = self.s3_service.download_file(self.feed_filename)
            fg = FeedGenerator()
            fg.load_extension('podcast')
            fg.parse_string(feed_content)
            return fg
        except Exception:
            print('no existing feed found, creating new one')
            return self._create_feed()
    
    def add_article_to_feed(self, article: Article):
        fg = self._get_existing_feed()
        
        fe = fg.add_entry()
        fe.id(str(article.id))
        fe.title(article.title)
        fe.description(article.content[:500] + '...' if len(article.content) > 500 else article.content)
        fe.link(href=article.content_url)
        
        # Add podcast-specific elements
        fe.enclosure(article.audio_url, 0, 'audio/mpeg')  # The '0' is for file size, which we could calculate if needed
        fe.published(datetime.now(timezone.utc))
        
        # Save the feed to a temporary file and upload to S3
        with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as temp_file:
            fg.rss_file(temp_file.name)
            self.s3_service.upload_file(temp_file.name, self.feed_filename)
            
        return self.s3_service.get_file_url(self.feed_filename) 