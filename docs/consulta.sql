SELECT 
		VTM.NO_NM as "Principio_ativo", 
        VMP.NO_NM as "Produto Medicinal Virtual" , 
        VMPP.NO_NM "Produto Medicinal Virtual com Apresentação",
        AMP.NO_NM "Produto Medicinal Comercial",
        AMPP.NO_NM "Produto Medicinal Comercial com Apresentação"
FROM obm.tb_vmp VMP
JOIN OBM.TB_VTM VTM
ON vmp.CO_VTMID = VTM.CO_SEQ_ID
JOIN OBM.tb_vmpp VMPP
ON vmp.CO_SEQ_ID = VMPP.CO_VPID
JOIN TB_AMP AMP
ON VMP.CO_SEQ_ID = AMP.CO_VPID
JOIN tb_ampp AMPP
ON AMP.CO_SEQ_ID = AMPP.CO_APID
where VTM.NO_NM like '%Bromoprida%'






-- WHERE VMP.CO_SEQ_ID = 11914
limit 1000