def set_tables(univ):
    if univ == 'LKHD':
        return ('lu', 'conf', 'lutoconf')
    if univ == 'CONF':
        return ('conf', 'lu', 'conftolu')
