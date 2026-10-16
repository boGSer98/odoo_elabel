def migrate(cr, version):
    cr.execute("SELECT elabel_token, array_agg(id ORDER BY id) FROM product_template WHERE elabel_token IS NOT NULL AND elabel_token != '' GROUP BY elabel_token HAVING count(*) > 1")
    conflicts=cr.fetchall()
    if conflicts:
        raise RuntimeError('e-Label: Tokenkollisionen vor Upgrade fachlich bereinigen. Betroffene Produktgruppen: %s' % [ids for token, ids in conflicts])
    cr.execute("UPDATE product_template SET elabel_token=NULL WHERE elabel_token=''")
