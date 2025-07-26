def generate_cot_prompt(reflection_text: str) -> str:
    """
    Chain-of-Thought (CoT) prompting template for judgment agent.
    1. 핵심 키워드 추출
    2. 긍정/부정 판단
    3. 개선점 제안
    """
    prompt = f"""회고 내용을 아래와 같이 단계별로 평가해주세요:
1. 핵심 키워드를 3개 선정하세요.
2. 각 키워드의 긍정적·부정적 맥락을 분석하세요.
3. 개선할 점을 구체적으로 제안하세요.

회고 내용:
""" + reflection_text + """ 

응답 형식:
1) 키워드: ...
2) 분석: ...
3) 개선 제안: ...
"""
    return prompt