from typing import TypedDict, Optional

class MyState(TypedDict):
    api_key: Optional[str]

    video_entrevista: Optional[str]
    mensagem_usuario: Optional[str]
    mensagem: Optional[str]
    estado: Optional[str]
    transcricao: Optional[str]
    minimundo: Optional[str]

    old_mw: Optional[str]
    mw_instruction: Optional[str]

    rascunho_requisitos: Optional[str]
    requisitos_tabelas: Optional[str]
    requisitos_priorizados: Optional[str]
    report: Optional[str]

    old_requirements: Optional[str]
    # requirements_instruction: Optional[str]

    ident_usecases: Optional[str]
    ident_events: Optional[str]
    report_validateuc: Optional[str]
    format_uc: Optional[str]
    usecases_diagram: Optional[str]

    old_uc: Optional[str]
    uc_information: Optional[str]

    rascunho_classes: Optional[str]
    diagrama_classes: Optional[str]
    diagrama_classes_revisado: Optional[str]
    diagrama_classes_final: Optional[str]

    old_cd: Optional[str]
    cd_instruction: Optional[str]

    cdinuc_description_revised: Optional[str]
    cdinuc_table_revised: Optional[str]
    cdinuc_diagram_revised: Optional[str]
    ucincd_revised: Optional[str]

    interface_prototype: Optional[str]
    interface_description: Optional[str]