from typing import Dict, Any, Optional
import logging
from .registry import BusinessTools
from .models import DocumentationInfo
from .utils import setup_logger

logger = setup_logger(__name__)

class DocumentationAnalyzer:
    def __init__(self, nlp_model=None):
        self.tools = BusinessTools.create()
        self.nlp_model = nlp_model 