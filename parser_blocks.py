import re
from typing import List, Dict

# ---------------------------------------------------------
# Generatoren für die einzelnen Blöcke
# ---------------------------------------------------------

def generate_itable(iname: str, tables: List[str]) -> str:
    """
    ITABLE-Block für alle verwendeten Tabellen.
    """
    header = 'INSERT INTO L2001.itable (I_name,Tbl_name,Tbl_alias,I_stichtag,Tabnr) VALUES (:1,:2,:3,:4,:5)\n\\\n$DATATYPES CHARACTER,CHARACTER,CHARACTER,CHARACTER,NUMERIC\n'
    lines = []
    for i, tbl in enumerate(tables, start=1):
        lines.append(f"\"{iname}\",\"{tbl}\",\"{tbl}\",\"1\",{i},")
    return header + "\n".join(lines) + "\n/"

def generate_ifield(iname: str, fields: List[str]) -> str:
    """
    IFIELD-Block für alle ausgewählten Felder.
    """
    header = 'INSERT INTO L2001.ifield (I_name,Tbl_name,Tbl_alias,F_dbcol,F_sel_nr,F_alias,F_dec,F_format,F_formatweb,F_sortierung,F_sort_nr,F_title,F_width,F_xmltag,F_translation,F_zwisnsum,F_literal) VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9,:10,:11,:12,:13,:14,:15,:16,:17)\n\\\n$DATATYPES CHARACTER,CHARACTER,CHARACTER,CHARACTER,NUMERIC,CHARACTER,NUMERIC,CHARACTER,CHARACTER,CHARACTER,NUMERIC,CHARACTER,NUMERIC,CHARACTER,CHARACTER,CHARACTER,CHARACTER\n'
    lines = []
    for i, f in enumerate(fields):
        tbl, col = f.split(".")
        lines.append(f"\"{iname}\",\"{tbl}\",\"{tbl}\",\"{col}\",{i},\"{col}\",,,,,,\"{col}\",,,")
    return header + "\n".join(lines) + "\n/"

def generate_ibeziehung(iname: str, joins: List[List[str]]) -> str:
    """
    IBEZIEHUNG-Block für alle Joins.
    """
    header = 'INSERT INTO L2001.ibeziehung (I_name,Tbl_name,Tbl_alias,F_dbcol,Tbl_name_nach,Tbl_alias_nach,F_dbcol_nach,Beznr,I_joinart) VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9)\n\\\n$DATATYPES CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER,NUMERIC,NUMERIC\n'
    lines = []
    for i, j in enumerate(joins, start=1):
        src_tbl, src_col, tgt_tbl, tgt_col = j
        lines.append(f"\"{iname}\",\"{src_tbl}\",\"{src_tbl}\",\"{src_col}\",\"{tgt_tbl}\",\"{tgt_tbl}\",\"{tgt_col}\",{i},1")
    return header + "\n".join(lines) + "\n/"

def generate_ibedingung(iname: str, conditions: List[str]) -> str:
    """
    IBEDINGUNG-Block für WHERE-Bedingungen.
    """
    header = 'INSERT INTO L2001.ibedingung (I_name,Tbl_name,Tbl_alias,F_dbcol,I_bednr,F_dbcol_2,I_aend,I_klammerauf,I_klammerzu,I_logop,I_op,Tbl_alias_2,Tbl_name_2,I_expression) VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9,:10,:11,:12,:13,:14)\n\\\n$DATATYPES CHARACTER,CHARACTER,CHARACTER,CHARACTER,NUMERIC,CHARACTER,CHARACTER,NUMERIC,NUMERIC,CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER\n'
    lines = []
    for i, cond in enumerate(conditions):
        lines.append(f"\"{iname}\",\"PGRDAT\",\"PGRDAT\",\"\",{i},,,0,0,,,,'','',{cond}")
    return header + "\n".join(lines) + "\n/"

# ---------------------------------------------------------
# Assembler
# ---------------------------------------------------------

def assemble_scout_file(iname: str, tables: List[str], fields: List[str], joins: List[List[str]], conditions: List[str]) -> str:
    """
    Fügt alle Blöcke zusammen zu einer vollständigen Scout-Importdatei.
    """
    blocks = []
    blocks.append(generate_itable(iname, tables))
    blocks.append(generate_ifield(iname, fields))
    if joins:
        blocks.append(generate_ibeziehung(iname, joins))
    if conditions:
        blocks.append(generate_ibedingung(iname, conditions))
    return "\n\n".join(blocks)
