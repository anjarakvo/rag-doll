import logging

from db import connect_to_sqlite, get_stable_prompt
from assistant import main, get_language, assistant_data, query_llm
from unittest.mock import patch, MagicMock


def test_connect_to_sqlite():
    conn = connect_to_sqlite()
    assert conn is not None


def test_get_stable_prompt():
    conn = connect_to_sqlite()
    prompt = get_stable_prompt(conn=conn, language="id")
    assert prompt is None

    prompt = get_stable_prompt(conn=conn, language="en")
    assert prompt is not None
    assert prompt["language"] == "en"
    assert prompt["system_prompt"] is not None
    assert prompt["rag_prompt"] is not None
    assert prompt["ragless_prompt"] is not None

    prompt = get_stable_prompt(conn=conn, language="fr")
    assert prompt is not None
    assert prompt["language"] == "fr"
    assert prompt["system_prompt"] is not None
    assert prompt["rag_prompt"] is not None
    assert prompt["ragless_prompt"] is not None

    prompt = get_stable_prompt(conn=conn, language="sw")
    assert prompt is not None
    assert prompt["language"] == "sw"
    assert prompt["system_prompt"] is not None
    assert prompt["rag_prompt"] is not None
    assert prompt["ragless_prompt"] is not None
    conn.close()


def test_language_support():
    main()
    conn = connect_to_sqlite()
    en_prompt = get_stable_prompt(conn=conn, language="en")
    fr_prompt = get_stable_prompt(conn=conn, language="fr")
    sw_prompt = get_stable_prompt(conn=conn, language="sw")
    conn.close()
    # not defined language default to english
    detected_language = get_language(
        "Halo, tolong kirimkan saya rekomendasi tentang pertanian di Kenya."
    )
    assert detected_language == "en"
    knowledge_base = assistant_data[detected_language]["knowledge_base"]
    system_prompt = assistant_data[detected_language]["system_prompt"]
    rag_prompt = assistant_data[detected_language]["rag_prompt"]
    ragless_prompt = assistant_data[detected_language]["ragless_prompt"]
    assert knowledge_base.name == "EPPO-datasheets-en"
    assert system_prompt == en_prompt["system_prompt"]
    assert rag_prompt == en_prompt["rag_prompt"]
    assert ragless_prompt == en_prompt["ragless_prompt"]

    detected_language = get_language(
        "Bonjour, veuillez m'envoyer les recommandations d'agriculture au Kenya"
    )
    assert detected_language == "fr"
    knowledge_base = assistant_data[detected_language]["knowledge_base"]
    system_prompt = assistant_data[detected_language]["system_prompt"]
    rag_prompt = assistant_data[detected_language]["rag_prompt"]
    ragless_prompt = assistant_data[detected_language]["ragless_prompt"]
    assert knowledge_base.name == "EPPO-datasheets-fr"
    assert system_prompt == fr_prompt["system_prompt"]
    assert rag_prompt == fr_prompt["rag_prompt"]
    assert ragless_prompt == fr_prompt["ragless_prompt"]

    detected_language = get_language(
        "Hello, please send me the recommendations of agriculture in Kenya"
    )
    assert detected_language == "en"
    knowledge_base = assistant_data[detected_language]["knowledge_base"]
    system_prompt = assistant_data[detected_language]["system_prompt"]
    rag_prompt = assistant_data[detected_language]["rag_prompt"]
    ragless_prompt = assistant_data[detected_language]["ragless_prompt"]
    assert knowledge_base.name == "EPPO-datasheets-en"
    assert system_prompt == en_prompt["system_prompt"]
    assert rag_prompt == en_prompt["rag_prompt"]
    assert ragless_prompt == en_prompt["ragless_prompt"]

    detected_language = get_language(
        "Hujambo, tafadhali nitumie mapendekezo ya kilimo nchini Kenya"
    )
    assert detected_language == "sw"
    knowledge_base = assistant_data[detected_language]["knowledge_base"]
    system_prompt = assistant_data[detected_language]["system_prompt"]
    rag_prompt = assistant_data[detected_language]["rag_prompt"]
    ragless_prompt = assistant_data[detected_language]["ragless_prompt"]
    assert knowledge_base.name == "EPPO-datasheets-sw"
    assert system_prompt == sw_prompt["system_prompt"]
    assert rag_prompt == sw_prompt["rag_prompt"]
    assert ragless_prompt == sw_prompt["ragless_prompt"]


def test_query_llm():
    with patch("assistant.OpenAI") as mock_openai:
        conn = connect_to_sqlite()
        en_prompt = get_stable_prompt(conn=conn, language="en")
        conn.close()

        mock_content = MagicMock()
        mock_content.content = "Mocked response"
        mock_choices = MagicMock()
        mock_choices.message = mock_content
        mock_response = MagicMock()
        mock_response.choices = [mock_choices]
        mock_response.created = 1643723400

        mock_openai.return_value.chat.completions.create.return_value = (
            mock_response
        )

        llm_client = mock_openai()
        model = "my_model"
        system_prompt = en_prompt["system_prompt"]
        ragless_prompt_template = en_prompt["ragless_prompt"]
        rag_prompt_template = en_prompt["rag_prompt"]
        context = ["Knowledge base chunk 1", "Knowledge base chunk 2"]
        prompt = (
            "Hello, please send me the recommendations of agriculture in Kenya"
        )

        history = [
            {"role": "system", "content": "Previous system message"},
            {"role": "user", "content": "Previous user query"},
            {"role": "assistant", "content": "Previous assistant response"},
        ]

        # Set up logger
        logger = logging.getLogger("assistant")
        logger.setLevel(logging.INFO)
        logger_handler = logging.StreamHandler()
        logger_handler.setLevel(logging.INFO)
        logger.addHandler(logger_handler)

        # Call query_llm function
        response, _ = query_llm(
            llm_client,
            model,
            system_prompt,
            ragless_prompt_template,
            rag_prompt_template,
            context,
            prompt,
            history,
        )

        # Check that llm_messages includes the history
        expected_llm_messages = (
            [
                {"role": "system", "content": system_prompt},
            ]
            + history
            + [
                {
                    "role": "user",
                    "content": rag_prompt_template.format(
                        prompt=prompt, context="\n".join(context)
                    ),
                },
            ]
        )
        # Check logger output
        logger_handler.stream.seek(0)
        logger_output = logger_handler.stream.read()
        expected_logger_output1 = f"[ASSISTANT] -> final prompt: {prompt}"
        expected_logger_output2 = (
            f"[ASSISTANT] -> query_llm with messages: {expected_llm_messages}"
        )

        assert expected_logger_output1 in logger_output
        assert expected_logger_output2 in logger_output
        assert response == "Mocked response"
