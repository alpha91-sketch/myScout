-- Scout-Export (Minimal-Template)
-- Basis für Generator – PGRDAT + VERTRAG

delete from L2001.iselect where i_name in ('99999999');
delete from L2001.ifrom where i_name in ('99999999');
delete from L2001.iwhere where i_name in ('99999999');
delete from L2001.igroup where i_name in ('99999999');
delete from L2001.iorder where i_name in ('99999999');
delete from L2001.iobjekte where i_name in ('99999999');
delete from L2001.ititel where i_name in ('99999999');
delete from L2001.ibedingung where i_name in ('99999999');
delete from L2001.itext where i_name in ('99999999');
delete from L2001.itemplateout where iname in ('99999999');

insert into L2001.ititel values ('99999999','TEMPLATE_MINIMAL');

insert into L2001.iselect values ('99999999',1,'PGRDAT.MAN');
insert into L2001.iselect values ('99999999',2,'PGRDAT.AK');
insert into L2001.iselect values ('99999999',3,'PGRDAT.PNR');
insert into L2001.iselect values ('99999999',4,'PGRDAT.NANAME');
insert into L2001.iselect values ('99999999',5,'PGRDAT.VORNAME');
insert into L2001.iselect values ('99999999',6,'VERTRAG.VERBEGIN');
insert into L2001.iselect values ('99999999',7,'VERTRAG.VERENDE');

insert into L2001.ifrom values ('99999999',1,'PGRDAT');
insert into L2001.ifrom values ('99999999',2,'VERTRAG');

insert into L2001.iwhere values ('99999999',1,'PGRDAT.MAN = VERTRAG.MAN');
insert into L2001.iwhere values ('99999999',2,'PGRDAT.AK = VERTRAG.AK');
insert into L2001.iwhere values ('99999999',3,'PGRDAT.PNR = VERTRAG.PNR');

insert into L2001.igroup values ('99999999',1,'1,2,3,4,5,6,7');
insert into L2001.iorder values ('99999999',1,'1,2,3,4,5,6,7');

insert into L2001.itemplateout values ('99999999','GENERATOR_TEMPLATE');

commit;
