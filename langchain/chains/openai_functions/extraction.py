from typing import Any, List

from pydantic import BaseModel

from langchain.base_language import BaseLanguageModel
from langchain.chains.base import Chain
from langchain.chains.llm import LLMChain
from langchain.chains.openai_functions.utils import (
    _convert_schema,
    _resolve_schema_references,
)
from langchain.output_parsers.openai_functions import (
    JsonKeyOutputFunctionsParser,
    PydanticAttrOutputFunctionsParser,
)
from langchain.prompts import ChatPromptTemplate

EXTRACTION_NAME = "information_extraction"
EXTRACTION_KWARGS = {"function_call": {"name": "information_extraction"}}


def _get_extraction_functions(entity_schema: dict) -> List[dict]:
    return [
        {
            "name": EXTRACTION_NAME,
            "description": "Extracts the relevant information from the passage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "info": {"type": "array", "items": _convert_schema(entity_schema)}
                },
                "required": ["info"],
            },
        }
    ]


_EXTRACTION_TEMPLATE = """Extract and save the relevant entities mentioned\
 in the following passage together with their properties.

Passage:
{input}
"""


def create_extraction_chain(schema: dict, llm: BaseLanguageModel) -> Chain:
    functions = _get_extraction_functions(schema)
    prompt = ChatPromptTemplate.from_template(_EXTRACTION_TEMPLATE)
    output_parser = JsonKeyOutputFunctionsParser(key_name="info")
    chain = LLMChain(
        llm=llm,
        prompt=prompt,
        llm_kwargs={**{"functions": functions}, **EXTRACTION_KWARGS},
        output_parser=output_parser,
    )
    return chain


def create_extraction_chain_pydantic(
    pydantic_schema: Any, llm: BaseLanguageModel
) -> Chain:
    class PydanticSchema(BaseModel):
        info: List[pydantic_schema]  # type: ignore

    openai_schema = PydanticSchema.schema()
    openai_schema = _resolve_schema_references(
        openai_schema, openai_schema["definitions"]
    )

    functions = _get_extraction_functions(openai_schema)
    prompt = ChatPromptTemplate.from_template(_EXTRACTION_TEMPLATE)
    output_parser = PydanticAttrOutputFunctionsParser(
        pydantic_schema=PydanticSchema, attr_name="info"
    )
    chain = LLMChain(
        llm=llm,
        prompt=prompt,
        llm_kwargs={**{"functions": functions}, **EXTRACTION_KWARGS},
        output_parser=output_parser,
    )
    return chain
