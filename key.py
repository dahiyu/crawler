# coding:utf-8

import os
import os.path
import dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
dotenv.load_dotenv(dotenv_path)

SPLA_SEARCH_RESULT_URL = os.environ.get("SPLA_SEARCH_RESULT_URL")
