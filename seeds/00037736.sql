/* TSMOD: 2025-09-20 21:47:38 */
/*Exported with LOGA Scout Export utility; Databasetype=PostgreSQL*/
call LOGALIB;
call QUIZLIB;
execsql delete from L2001.ITABLE where i_name IN ('00037736');
execsql delete from L2001.IBEDINGUNG where i_name IN ('00037736');
execsql delete from L2001.IBEZIEHUNG where i_name IN ('00037736');
execsql delete from L2001.IQUERYPARAM where i_name IN ('00037736');
execsql delete from L2001.ICHILD where i_name IN ('00037736');
execsql delete from L2001.IEXPLMEMBER where i_name IN ('00037736');
execsql delete from L2001.IFIELD where i_name IN ('00037736');
execsql delete from L2001.IFKTMEMBER where i_name IN ('00037736');
execsql delete from L2001.IFORMEL where i_name IN ('00037736');
execsql delete from L2001.IMASKMEMBER where i_name IN ('00037736');
execsql delete from L2001.ITEMPLATEOUT where iname IN ('00037736');
execsql delete from L2001.IMEMBER where i_name IN ('00037736');
/OPTION UPDATE
set work.tabsize=1
INSERT INTO L2001.imember (I_name,I_bez,Bereich,Bergrp,Called_by,Cid_man,Cls_lastupd,Cls_lvl,Cls_maxsub,Cls_numfunc,C_name,I_aender,I_anzeige,I_anzges,I_author,I_batch,I_del,I_delimiter,I_distinct,I_dok,I_erstell,I_info,I_krit,I_maxcost,I_maxrows,I_moshift,I_privat,I_pro,I_quota,I_search,I_sum,I_text,I_unionall,I_version,Sek_i_name,I_nutzung_bes,I_ergebnis_bes,I_ausgdok,I_qrtimeout,Iscout_used,Iscout_use_it,I_escaper,I_replacedby,I_replacement,Iscouthash,Hr_ap,I_anzkrpar,I_uaonly,Promoted,I_encoding,I_pgsettings,I_opersys,I_hrklasse,Hidden,I_stichtag_aend,I_fetchall,I_infolong) VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9,:10,:11,:12,:13,:14,:15,:16,:17,:18,:19,:20,:21,:22,:23,:24,:25,:26,:27,:28,:29,:30,:31,:32,:33,:34,:35,:36,:37,:38,:39,:40,:41,:42,:43,:44,:45,:46,:47,:48,:49,:50,:51,:52,:53,:54,:55,:56,:57)
\
$DATATYPES CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER,DATE,CHARACTER,NUMERIC,NUMERIC,CHARACTER,DATE,CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER,DATE,CHARACTER,CHARACTER,NUMERIC,NUMERIC,CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER,NUMERIC,CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER,NUMERIC,CHARACTER,CHARACTER,CHARACTER,CHARACTER,NUMERIC,CHARACTER,NUMERIC,CHARACTER
"00037736","Aufg_1_Standard_MA_Vertr.","RUNZI_TEST","USER",,,,,,,,2024-07-01,"ANZ","0","428956.63000.40",,"0",,"0",,2024-02-26,,"KEINE",0,0,,"0",,"NEIN",,"LISTE",,"0",,,,,,0,,"0",,,,,"[]","0","0",,,,,,,,,$long,
//
/
/OPTION UPDATE
set work.tabsize=0
INSERT INTO L2001.itemplateout (Iname,Man,Ak,Pnr,Customer,Filename,Filetype,Templatedata) VALUES (:1,:2,:3,:4,:5,:6,:7,:8)
\
$DATATYPES CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER
/
/OPTION UPDATE
set work.tabsize=0
INSERT INTO L2001.imaskmember (I_name,Msk_id) VALUES (:1,:2)
\
$DATATYPES CHARACTER,CHARACTER
/
/OPTION UPDATE
set work.tabsize=0
INSERT INTO L2001.iformel (I_name,I_form,I_formnr,F_dbcol,I_expression,I_klammerauf,I_klammerzu,I_op,I_scale,I_size,I_type,Tbl_alias,Tbl_name) VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9,:10,:11,:12,:13)
\
$DATATYPES CHARACTER,CHARACTER,NUMERIC,CHARACTER,CHARACTER,NUMERIC,NUMERIC,CHARACTER,NUMERIC,NUMERIC,CHARACTER,CHARACTER,CHARACTER
/
/OPTION UPDATE
set work.tabsize=0
INSERT INTO L2001.ifktmember (I_name,Fkt_name,I_paranr,I_parameter,I_src_field,I_src_tab) VALUES (:1,:2,:3,:4,:5,:6)
\
$DATATYPES CHARACTER,CHARACTER,NUMERIC,CHARACTER,CHARACTER,CHARACTER
/
/OPTION UPDATE
set work.tabsize=7
INSERT INTO L2001.ifield (I_name,Tbl_name,Tbl_alias,F_dbcol,F_sel_nr,F_alias,F_dec,F_format,F_formatweb,F_sortierung,F_sort_nr,F_title,F_width,F_xmltag,F_translation,F_zwisnsum,F_literal) VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9,:10,:11,:12,:13,:14,:15,:16,:17)
\
$DATATYPES CHARACTER,CHARACTER,CHARACTER,CHARACTER,NUMERIC,CHARACTER,NUMERIC,CHARACTER,CHARACTER,CHARACTER,NUMERIC,CHARACTER,NUMERIC,CHARACTER,CHARACTER,CHARACTER,CHARACTER
"00037736","PGRDAT","PGRDAT","AK",1,"AK",,"10000","100000",,-1,"Abrechnungskreis",5.00000000,"pjak",,,,
"00037736","PGRDAT","PGRDAT","MAN",0,"MAN",,"10000","100000",,-1,"Mandant",5.00000000,"pjman",,,,
"00037736","PGRDAT","PGRDAT","NANAME",3,"NANAME",,"10000","100000",,-1,"Nachname",110.00000000,"qnaname",,,,
"00037736","PGRDAT","PGRDAT","PNR",2,"PNR",,"10000","100000",,-1,"personalnummer",12.00000000,"qpnr",,,,
"00037736","PGRDAT","PGRDAT","VORNAME",4,"VORNAME",,"10000","100000",,-1,"Vorname",110.00000000,"qnamevor",,,,
"00037736","VERTRAG","VERTRAG","VERBEGIN",5,"VERBEGIN",,"10000","100000",,-1,"Vertragsbeginn",4.00000000,"vbbegin",,,,
"00037736","VERTRAG","VERTRAG","VERENDE",6,"VERENDE",,"10000","100000",,-1,"Vertragsende",4.00000000,"vbende",,,,
/
/OPTION UPDATE
set work.tabsize=0
INSERT INTO L2001.iexplmember (I_name,Expl_id) VALUES (:1,:2)
\
$DATATYPES CHARACTER,CHARACTER
/
/OPTION UPDATE
set work.tabsize=0
INSERT INTO L2001.ichild (I_name,I_child,I_paranr,I_src_field,I_src_tab,I_trg_field,I_trg_tab) VALUES (:1,:2,:3,:4,:5,:6,:7)
\
$DATATYPES CHARACTER,CHARACTER,NUMERIC,CHARACTER,CHARACTER,CHARACTER,CHARACTER
/
/OPTION UPDATE
set work.tabsize=0
INSERT INTO L2001.iqueryparam (I_name,Paramlfd,Paramname,U_id,I_type,I_defdat,I_defint,I_defnum,I_defstr,I_modus) VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9,:10)
\
$DATATYPES CHARACTER,NUMERIC,CHARACTER,CHARACTER,CHARACTER,DATE,NUMERIC,NUMERIC,CHARACTER,CHARACTER
/
/OPTION UPDATE
set work.tabsize=3
INSERT INTO L2001.ibeziehung (I_name,Tbl_name,Tbl_alias,F_dbcol,Tbl_name_nach,Tbl_alias_nach,F_dbcol_nach,Beznr,I_joinart) VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9)
\
$DATATYPES CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER,NUMERIC,NUMERIC
"00037736","PGRDAT","PGRDAT","AK","VERTRAG","VERTRAG","AK",2,1,
"00037736","PGRDAT","PGRDAT","MAN","VERTRAG","VERTRAG","MAN",1,1,
"00037736","PGRDAT","PGRDAT","PNR","VERTRAG","VERTRAG","PNR",3,1,
/
/OPTION UPDATE
set work.tabsize=3
INSERT INTO L2001.ibedingung (I_name,Tbl_name,Tbl_alias,F_dbcol,I_bednr,F_dbcol_2,I_aend,I_klammerauf,I_klammerzu,I_logop,I_op,Tbl_alias_2,Tbl_name_2,I_expression) VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9,:10,:11,:12,:13,:14)
\
$DATATYPES CHARACTER,CHARACTER,CHARACTER,CHARACTER,NUMERIC,CHARACTER,CHARACTER,NUMERIC,NUMERIC,CHARACTER,CHARACTER,CHARACTER,CHARACTER,CHARACTER
"00037736","PGRDAT","PGRDAT","Abrechnungskreis                        AK",1,,"1",0,0,"and","=",,,"70",
"00037736","PGRDAT","PGRDAT","Mandant                                 MAN",0,,"1",0,0,"and","=",,,"63000",
"00037736","VERTRAG","VERTRAG","Historisches Bis-Datum                  VER_BIS",2,,"1",0,0,,">=",,,"31.01.2099",
/
/OPTION UPDATE
set work.tabsize=2
INSERT INTO L2001.itable (I_name,Tbl_name,Tbl_alias,I_stichtag,Tabnr) VALUES (:1,:2,:3,:4,:5)
\
$DATATYPES CHARACTER,CHARACTER,CHARACTER,CHARACTER,NUMERIC
"00037736","PGRDAT","PGRDAT","1",1,
"00037736","VERTRAG","VERTRAG","1",2,
/
execsql update L2001.itemplateout set MAN='___MAN___', AK='___AK___', PNR='___PNR___', CUSTOMER='___CUSTOMER___' where INAME in ('00037736');
execsql update L2001.imember set I_PRIVAT='1', I_AUTHOR='___I_AUTHOR___', BERGRP='___BERGRP___', BEREICH='___BEREICH___' where I_NAME in ('00037736');
