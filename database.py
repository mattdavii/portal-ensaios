import sqlite3

def get_db_connection():
    conn = sqlite3.connect('ensaios_eletricos.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def criar_tabelas():
    conn = get_db_connection()
    cursor = conn.cursor()
    # 1. Trafo, TP e TC
    cursor.execute('''CREATE TABLE IF NOT EXISTS ensaio_final (id INTEGER PRIMARY KEY AUTOINCREMENT, usina TEXT, tag TEXT, tipo TEXT, tap TEXT, nom_pri REAL, nom_sec REAL, rn_teorico REAL, ttr_a REAL, ttr_b REAL, ttr_c REAL, status_ttr TEXT, h1 REAL, h2 REAL, h3 REAL, uni_h TEXT, status_h TEXT, x1 REAL, x2 REAL, x3 REAL, uni_x TEXT, status_x TEXT, at_t REAL, at_bt REAL, bt_t REAL, status_at_t TEXT, status_at_bt TEXT, status_bt_t TEXT, data TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    # 2 a 4. Disjuntores e Seccionadoras
    for tab in ['ensaio_disjuntor_mt', 'ensaio_seccionadora', 'ensaio_disjuntor_bt']:
        cursor.execute(f'''CREATE TABLE IF NOT EXISTS {tab} (id INTEGER PRIMARY KEY AUTOINCREMENT, usina TEXT, tag TEXT, fabricante TEXT, res_c_r REAL, res_c_s REAL, res_c_t REAL, status_contato TEXT, iso_ft_r REAL, iso_ft_s REAL, iso_ft_t REAL, status_iso_ft TEXT, iso_ff_rs REAL, iso_ff_st REAL, iso_ff_tr REAL, status_iso_ff TEXT, iso_ab_r REAL, iso_ab_s REAL, iso_ab_t REAL, status_iso_ab TEXT, data TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # 5. Cabos CC (NOVO: Adicionado skid e inversor)
    cursor.execute('''CREATE TABLE IF NOT EXISTS ensaio_cabos_cc (id INTEGER PRIMARY KEY AUTOINCREMENT, usina TEXT, skid TEXT, inversor TEXT, tag TEXT, origem TEXT, destino TEXT, voc REAL, v_pos_terra REAL, v_neg_terra REAL, status_pos TEXT, status_neg TEXT, status_geral TEXT, data TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # 6. Continuidade Malha
    cursor.execute('''CREATE TABLE IF NOT EXISTS ensaio_cont_malha (id INTEGER PRIMARY KEY AUTOINCREMENT, usina TEXT, tag TEXT, pt1_nome TEXT, pt1_res REAL, pt2_nome TEXT, pt2_res REAL, pt3_nome TEXT, pt3_res REAL, status_geral TEXT, data TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    # 7. Resistência Malha
    cursor.execute('''CREATE TABLE IF NOT EXISTS ensaio_res_malha (id INTEGER PRIMARY KEY AUTOINCREMENT, usina TEXT, tag TEXT, metodo TEXT, d_total REAL, r52 REAL, r62 REAL, r72 REAL, r_media REAL, desvio REAL, status_plat TEXT, status_geral TEXT, data TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()