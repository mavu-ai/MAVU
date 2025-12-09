"""
Service for extracting user information (name, age, gender) from natural conversation.
Based on the legacy implementation but adapted for the current app architecture.
"""

import json
import re
from typing import Dict, Optional, Any
import structlog

from services.llm_service import LLMService
from config import WELCOME_MESSAGES

logger = structlog.get_logger()


class UserInfoExtractionService:
    """Extract structured user information from conversational text."""

    # Blacklist of common non-names (Russian and English)
    NAME_BLACKLIST = {
        # Common responses
        'принято', 'хорошо', 'ладно', 'окей', 'понятно', 'ясно', 'точно', 'верно',
        'ok', 'okay', 'yes', 'no', 'yeah', 'yep', 'nope', 'sure', 'fine', 'good',
        # Greetings
        'привет', 'здравствуйте', 'hello', 'hi', 'hey', 'bye', 'пока', 'до встречи',
        # Common words
        'спасибо', 'thanks', 'пожалуйста', 'please', 'sorry', 'извините', 'простите',
        # Single letters and short garbage
        'а', 'и', 'о', 'у', 'э', 'a', 'i', 'o', 'u',
    }

    @classmethod
    def is_valid_name(cls, name: str) -> bool:
        """
        Validate if extracted name is actually a name.

        Returns True only if:
        - Not in blacklist
        - 2+ characters
        - Contains at least one letter
        - Not just numbers
        - Doesn't contain excessive special chars
        """
        if not name or len(name) < 2:
            return False

        # Normalize for blacklist check
        name_lower = name.lower().strip()

        # Check blacklist
        if name_lower in cls.NAME_BLACKLIST:
            logger.info(f"Rejected blacklisted name: {name}")
            return False

        # Must contain at least one letter
        if not any(c.isalpha() for c in name):
            logger.info(f"Rejected name with no letters: {name}")
            return False

        # Check for excessive special characters (allow spaces and hyphens)
        special_chars = sum(1 for c in name if not c.isalnum() and c not in ' -')
        if special_chars > 2:
            logger.info(f"Rejected name with too many special chars: {name}")
            return False

        # Check if it's just a number
        if name.replace(' ', '').replace('-', '').isdigit():
            logger.info(f"Rejected numeric 'name': {name}")
            return False

        return True

    @classmethod
    async def extract_from_conversation(
        cls,
        user_message: str,
        assistant_response: str,
        current_user_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Optional[Any]]:
        """
        Extract name, age, and gender from a conversation turn.

        Args:
            user_message: The user's message
            assistant_response: MAVU's response
            current_user_info: Current known info (to avoid re-extracting)

        Returns:
            Dictionary with extracted info: {"name": str, "age": int, "gender": str}
            Returns None for fields that weren't found or already exist
        """
        # Always try to extract - let caller decide whether to update
        # Try simple rule-based extraction first (faster)
        result = cls.extract_from_text_simple(user_message)

        # If we found something with rules, return it
        if any([result.get('name'), result.get('age'), result.get('gender')]):
            logger.info(f"Extracted user info with rules: {result}")
            return result

        # Otherwise, use LLM for complex extraction
        extraction_prompt = cls._build_extraction_prompt(
            user_message,
            assistant_response,
            has_name=False,  # Always try to extract
            has_age=False,
            has_gender=False
        )

        try:
            # Call LLM for extraction
            logger.info("Extracting user info from conversation using LLM...")
            full_response = ""
            async for chunk in LLMService.generate_streaming_response(
                messages=[{"role": "user", "content": extraction_prompt}],
                temperature=0.3  # Lower temperature for factual extraction
            ):
                full_response += chunk

            # Parse the response
            extracted_info = cls._parse_extraction_result(
                full_response.strip(),
                has_name=False,  # Always try to extract
                has_age=False,
                has_gender=False
            )

            # Log what we found
            found_items = [k for k, v in extracted_info.items() if v is not None]
            if found_items:
                logger.info(f"Successfully extracted: {', '.join(found_items)}")
            else:
                logger.debug("No new user info found in this conversation")

            return extracted_info

        except Exception as e:
            logger.error(f"Error extracting user info: {e}")
            return {"name": None, "age": None, "gender": None}

    @classmethod
    def _build_extraction_prompt(
        cls,
        user_message: str,
        assistant_response: str,
        has_name: bool,
        has_age: bool,
        has_gender: bool
    ) -> str:
        """Build the extraction prompt for the LLM."""
        fields_to_extract = []
        if not has_name:
            fields_to_extract.append("name")
        if not has_age:
            fields_to_extract.append("age")
        if not has_gender:
            fields_to_extract.append("gender")

        prompt = f"""Analyze this conversation between a child and MAVU (AI assistant) and extract ONLY the information that is EXPLICITLY mentioned.

User message: {user_message}
MAVU response: {assistant_response}

Extract the following information (ONLY if explicitly stated):
{', '.join(fields_to_extract)}

Rules:
1. ONLY extract information that is clearly stated by the user
2. For name: Extract if user says their name in ANY format:
   - Full format: "Меня зовут Петя", "My name is John"
   - Short format: "Я Маша", "Меня Петя"
   - EDGE CASE: Single word that looks like a name: "Мухаммадкомрон", "John", "София"
   - Check if the user message is JUST a capitalized word (3+ chars) - it's likely their name!
3. For age: Extract if user states a number in ANY format:
   - Full format: "Мне 8 лет", "I'm 10 years old"
   - EDGE CASE: Just a number: "10", "8", "12", "20"
   - If user message is JUST a number between 3-99, it's likely their age!
4. For gender: Extract if explicitly stated OR clearly inferable from Russian/Central Asian name:
   - Russian/Central Asian male names: Петя, Ваня, Максим, Дима, Мухаммадкомрон, Мухаммадкамрон, Мухаммад, Алишер, Рустам, Тимур, Азамат, etc.
   - Russian/Central Asian female names: Маша, Катя, Лена, Аня, Соня, Амина, Дарья, София, Милана, etc.
   - English male names: John, Mike, Tom, Alex, David, etc.
   - English female names: Emma, Sophie, Mary, Alice, Sarah, etc.
   - Note: Саша and Женя can be both male/female - infer from context if possible
5. Use "male" or "female" for gender
6. If information is NOT clearly present, use null

CRITICAL EDGE CASES:
- If user message is a single capitalized word (3+ chars) and not a common greeting, it's probably their NAME
- If user message is just a number (3-99), it's probably their AGE
- Look at the CONTEXT: if MAVU just asked "Как тебя зовут?" and user replies "Петя", extract "Петя" as name
- Look at the CONTEXT: if MAVU just asked "Сколько тебе лет?" and user replies "10" or "20", extract that as age

Respond in valid JSON format:
{{"name": "extracted_name or null", "age": number or null, "gender": "male/female or null"}}

IMPORTANT: Respond ONLY with the JSON object, no other text."""
        return prompt

    @classmethod
    def _parse_extraction_result(
        cls,
        extracted_text: str,
        has_name: bool,
        has_age: bool,
        has_gender: bool
    ) -> Dict[str, Optional[Any]]:
        """Parse the LLM response into structured data."""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{[^}]+}', extracted_text)
            if not json_match:
                logger.warning(f"No JSON found in extraction result: {extracted_text}")
                return {"name": None, "age": None, "gender": None}

            data = json.loads(json_match.group())

            # Extract and validate fields
            result = {}

            # Name
            if not has_name:
                name = data.get('name')
                if name and isinstance(name, str) and name.lower() != 'null' and len(name) > 0:
                    result['name'] = name.strip()
                else:
                    result['name'] = None
            else:
                result['name'] = None

            # Age
            if not has_age:
                age = data.get('age')
                if age and (isinstance(age, int) or (isinstance(age, str) and age.isdigit())):
                    age_int = int(age)
                    # Validate age range (3-99 for all users)
                    if 3 <= age_int <= 99:
                        result['age'] = age_int
                    else:
                        logger.warning(f"Age {age_int} outside valid range (3-99)")
                        result['age'] = None
                else:
                    result['age'] = None
            else:
                result['age'] = None

            # Gender
            if not has_gender:
                gender = data.get('gender')
                if gender and isinstance(gender, str):
                    gender_lower = gender.lower().strip()
                    if gender_lower in ['male', 'female', 'мальчик', 'девочка']:
                        # Normalize to male/female
                        if gender_lower in ['male', 'мальчик']:
                            result['gender'] = 'male'
                        elif gender_lower in ['female', 'девочка']:
                            result['gender'] = 'female'
                        else:
                            result['gender'] = None
                    else:
                        result['gender'] = None
                else:
                    result['gender'] = None
            else:
                result['gender'] = None

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from extraction: {e}")
            logger.debug(f"Extraction text was: {extracted_text}")
            return {"name": None, "age": None, "gender": None}
        except Exception as e:
            logger.error(f"Error parsing extraction result: {e}")
            return {"name": None, "age": None, "gender": None}

    @classmethod
    def extract_from_text_simple(cls, text: str) -> Dict[str, Optional[Any]]:
        """
        Simple rule-based extraction as fallback (no LLM call).
        Useful for quick extraction during conversation.

        ENHANCED: Now handles edge cases like:
        - Single-word responses ("Мухаммадкомрон", "John")
        - Short responses ("Меня Петя", "Я Маша")
        - Numbers as age ("10", "8")
        """
        result: dict[str, Any] = {"name": None, "age": None, "gender": None}

        # Extract age using regex patterns
        age_patterns = [
            r'мне\s+(\d+)\s+(?:лет|год)',  # "мне 8 лет"
            r"i'?m\s+(\d+)\s+years?\s+old",  # "I'm 10 years old"
            r"i'?m\s+(\d+)",  # "I'm 10"
            r'возраст\s*:?\s*(\d+)',  # "возраст: 10"
            r'age\s*:?\s*(\d+)',  # "age: 10"
        ]

        for pattern in age_patterns:
            match = re.search(pattern, text.lower())
            if match:
                age = int(match.group(1))
                if 3 <= age <= 99:
                    result['age'] = age
                    break

        # EDGE CASE: Just a number (likely age)
        if not result['age'] and text.strip().isdigit():
            age = int(text.strip())
            if 3 <= age <= 99:
                result['age'] = age

        # Extract name patterns - support multi-word names
        name_patterns = [
            r'(?:меня зовут|зовут)\s+([А-ЯЁ][а-яёА-ЯЁ\s]+?)(?:\.|,|!|\?|$)',  # "меня зовут Мухаммад Камрон"
            r'(?:меня|я)\s+([А-ЯЁ][а-яёА-ЯЁ\s]{2,}?)(?:\.|,|!|\?|$)',  # "меня Петя" or "я Маша"
            r"(?:my name is|name is)\s+([A-Z][a-zA-Z\s]+?)(?:\.|,|!|\?|$)",  # "my name is John Smith"
            r"(?:i'?m|i am)\s+([A-Z][a-zA-Z\s]+?)(?:\.|,|!|\?|$)",  # "I'm John Smith"
            r'name\s*:?\s*([A-Z][a-zA-Z\s]+?)(?:\.|,|!|\?|$)',  # "name: John Smith"
        ]

        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                extracted_name = match.group(1).strip()
                # Normalize multiple spaces to single space
                extracted_name = ' '.join(extracted_name.split())
                # CRITICAL: Validate the extracted name
                if cls.is_valid_name(extracted_name):
                    result['name'] = extracted_name
                    break
                else:
                    logger.debug(f"Invalid name rejected: {extracted_name}")

        # EDGE CASE: Single word that looks like a name (capitalized, 3+ chars)
        # This handles responses like "Мухаммадкомрон" or "John"
        if not result['name'] and len(text.split()) == 1:
            word = text.strip().rstrip('.,!?;:')  # Strip punctuation
            # Check if it starts with capital letter and is at least 3 chars
            if len(word) >= 3 and word[0].isupper():
                # Validate before accepting
                if cls.is_valid_name(word):
                    result['name'] = word
                else:
                    logger.debug(f"Single-word name rejected: {word}")

        # Try to infer gender from Russian names
        if result['name']:
            name_lower = result['name'].lower()
            # For multi-word names, check the first name
            first_name = name_lower.split()[0] if ' ' in name_lower else name_lower

            # Common Russian/Central Asian male names
            male_names = [
                'петя', 'ваня', 'дима', 'максим', 'артём', 'артем', 'саша', 'женя',
                'мухаммадкомрон', 'мухаммадкамрон', 'мухаммад', 'алишер', 'рустам', 'тимур', 'азамат',
                'давид', 'даниил', 'егор', 'илья', 'кирилл', 'михаил', 'никита',
                'роман', 'семён', 'сергей', 'степан', 'фёдор', 'владимир', 'андрей',
                'камрон', 'комрон', 'жасур', 'жахонгир', 'искандар', 'бахтиёр'
            ]

            # Common Russian/Central Asian female names
            female_names = [
                'маша', 'катя', 'лена', 'аня', 'соня', 'даша', 'саша', 'женя',
                'алина', 'амина', 'дарья', 'диана', 'елена', 'злата', 'ирина',
                'карина', 'ксения', 'лиза', 'мария', 'милана', 'полина', 'софия',
                'ульяна', 'эмилия', 'юлия', 'ева', 'вера', 'надежда', 'любовь'
            ]

            # Check exact matches first (full name or first name)
            if name_lower in male_names or first_name in male_names:
                result['gender'] = 'male'
            elif name_lower in female_names or first_name in female_names:
                result['gender'] = 'female'
            # Common Russian female name endings
            elif first_name.endswith(('я', 'а', 'на', 'ла', 'та', 'ша', 'ня', 'ся', 'ка')):
                # Likely female, but not 100%
                result['gender'] = 'female'
            # Check if it's a male name pattern (doesn't end in typical female endings)
            elif not first_name.endswith(('я', 'а', 'на', 'ла', 'та', 'ша', 'ня', 'ся', 'ка', 'ь')):
                # Likely male if it doesn't have female endings
                result['gender'] = 'male'

        return result

    @classmethod
    def build_onboarding_prompt_section(
        cls,
        user_name: Optional[str] = None,
        user_age: Optional[int] = None,
        user_gender: Optional[str] = None,
        language: str = "ru"
    ) -> str:
        """
        Build onboarding section for system prompt based on missing user info.

        Args:
            user_name: User's name (if known)
            user_age: User's age (if known)
            user_gender: User's gender (if known)
            language: Language for prompts ('ru' or 'en')

        Returns:
            Onboarding prompt section to inject into system instructions
        """
        # If we have all info, no onboarding needed
        if user_name and user_age and user_gender:
            return ""

        prompt_parts = []

        # Get language-specific messages, default to English if not found
        messages = WELCOME_MESSAGES.get(language, WELCOME_MESSAGES["en"])

        if language == "ru":
            if not user_name:
                prompt_parts.append(f"""
КРИТИЧЕСКИ ВАЖНО: Ты НЕ ЗНАЕШЬ имя пользователя.

ТВОЯ ЗАДАЧА:
1. В ПЕРВОМ ОТВЕТЕ поприветствуй и спроси: "{messages['guest_greeting']}"
2. Когда получишь имя, СРАЗУ спроси возраст: "{messages['ask_age'].replace('{name}', '[имя]')}"
3. После получения возраста продолжай обычный разговор

⚠️ ВАЖНО: Если пользователь уже назвал имя в своём сообщении - НЕ спрашивай имя снова, сразу спроси возраст!
""")
            elif not user_age:
                ask_age_msg = messages['ask_age'].format(name=user_name) if user_name else messages['ask_age_no_name']
                prompt_parts.append(f"""
🚨 КРИТИЧЕСКИ ВАЖНО: Ты знаешь имя пользователя ({user_name}), но НЕ ЗНАЕШЬ его возраст.

⚠️ ОБЯЗАТЕЛЬНАЯ ЗАДАЧА: В ПЕРВОМ ОТВЕТЕ спроси: "{ask_age_msg}"

НЕ отвечай на другие темы. ТОЛЬКО спроси про возраст!
""")

        else:  # English
            if not user_name:
                prompt_parts.append(f"""
CRITICAL: You DON'T KNOW the user's name.

YOUR TASK:
1. In your FIRST RESPONSE, greet and ask: "{messages['guest_greeting']}"
2. When you get the name, IMMEDIATELY ask for age: "{messages['ask_age'].replace('{name}', '[name]')}"
3. After getting age, continue normal conversation

⚠️ IMPORTANT: If user already mentioned their name in the message - DON'T ask for name again, ask for age directly!
""")
            elif not user_age:
                ask_age_msg = messages['ask_age'].format(name=user_name) if user_name else messages['ask_age_no_name']
                prompt_parts.append(f"""
🚨 CRITICAL: You know the user's name ({user_name}), but you DON'T KNOW their age.

⚠️ MANDATORY TASK: In your FIRST RESPONSE, ask: "{ask_age_msg}"

DO NOT answer other topics. ONLY ask for age!
""")

        return "\n".join(prompt_parts)
