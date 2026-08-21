import sqlite3
DB_PATH='ensaios_eletricos.db'
def get_db_connection():
    conn=sqlite3.connect(DB_PATH,check_same_thread=False);conn.row_factory=sqlite3.Row;return conn
def _cols(conn,t):return {r['name'] for r in conn.execute(f'PRAGMA table_info({t})').fetchall()}
def _add(conn,t,n,sqltype):
    if n not in _cols(conn,t):conn.execute(f'ALTER TABLE {t} ADD COLUMN {n} {sqltype}')
def criar_tabelas():
    conn=get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS ensaio_final (id INTEGER PRIMARY KEY AUTOINCREMENT,usina TEXT,tag TEXT,tipo TEXT,tap TEXT,nom_pri REAL,nom_sec REAL,rn_teorico REAL,ttr_a REAL,ttr_b REAL,ttr_c REAL,status_ttr TEXT,h1 REAL,h2 REAL,h3 REAL,uni_h TEXT,status_h TEXT,x1 REAL,x2 REAL,x3 REAL,uni_x TEXT,status_x TEXT,at_t REAL,at_bt REAL,bt_t REAL,status_at_t TEXT,status_at_bt TEXT,status_bt_t TEXT,data TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    for t in ['ensaio_disjuntor_mt','ensaio_seccionadora','ensaio_disjuntor_bt']:
        conn.execute(f'''CREATE TABLE IF NOT EXISTS {t} (id INTEGER PRIMARY KEY AUTOINCREMENT,usina TEXT,tag TEXT,fabricante TEXT,res_c_r REAL,res_c_s REAL,res_c_t REAL,status_contato TEXT,iso_ft_r REAL,iso_ft_s REAL,iso_ft_t REAL,status_iso_ft TEXT,iso_ff_rs REAL,iso_ff_st REAL,iso_ff_tr REAL,status_iso_ff TEXT,iso_ab_r REAL,iso_ab_s REAL,iso_ab_t REAL,status_iso_ab TEXT,data TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS ensaio_cabos_cc (id INTEGER PRIMARY KEY AUTOINCREMENT,usina TEXT,skid TEXT,inversor TEXT,tag TEXT,origem TEXT,destino TEXT,voc REAL,v_pos_terra REAL,v_neg_terra REAL,n_modulos INTEGER,voc_stc REAL,beta_voc REAL,t_medida REAL,voc_esperada REAL,status_pos TEXT,status_neg TEXT,status_consistencia TEXT,status_voc TEXT,status_geral TEXT,data TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS ensaio_cont_malha (id INTEGER PRIMARY KEY AUTOINCREMENT,usina TEXT,tag TEXT,pt1_nome TEXT,pt1_res REAL,pt2_nome TEXT,pt2_res REAL,pt3_nome TEXT,pt3_res REAL,status_geral TEXT,data TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS ensaio_res_malha (id INTEGER PRIMARY KEY AUTOINCREMENT,usina TEXT,tag TEXT,metodo TEXT,d_total REAL,r52 REAL,r62 REAL,r72 REAL,r_media REAL,desvio REAL,status_plat TEXT,status_geral TEXT,data TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    comuns={'tecnico':'TEXT','os':'TEXT','observacoes':'TEXT','status_geral_v2':'TEXT'}
    tabelas=['ensaio_final','ensaio_disjuntor_mt','ensaio_disjuntor_bt','ensaio_seccionadora','ensaio_cabos_cc','ensaio_cont_malha','ensaio_res_malha']
    for t in tabelas:
        for n,tp in comuns.items():_add(conn,t,n,tp)
    for n,tp in {'classe':'TEXT','finalidade':'TEXT','temperatura_c':'REAL','tensao_ensaio_isolamento_v':'REAL','limite_ttr_pct':'REAL'}.items():_add(conn,'ensaio_final',n,tp)
    for t in ['ensaio_disjuntor_mt','ensaio_disjuntor_bt','ensaio_seccionadora']:
        _add(conn,t,'corrente_ensaio_a','REAL');_add(conn,t,'tensao_ensaio_isolamento_v','REAL');_add(conn,t,'desequilibrio_pct','REAL')
    for n,tp in {'temperatura_modulo':'REAL','tolerancia_voc':'REAL','riso_mohm':'REAL','tensao_riso_v':'REAL','erro_fechamento_pct':'REAL','diagnostico':'TEXT','status_riso':'TEXT'}.items():_add(conn,'ensaio_cabos_cc',n,tp)
    _add(conn,'ensaio_res_malha','status_valor','TEXT')

    conn.execute("""
        CREATE TABLE IF NOT EXISTS ensaio_riso_strings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usina TEXT,
            tag TEXT,
            inversor TEXT,
            riso_pos_mohm REAL,
            riso_neg_mohm REAL,
            tensao_ensaio_v REAL,
            status_pos TEXT,
            status_neg TEXT,
            status_geral TEXT,
            tecnico TEXT,
            os TEXT,
            observacoes TEXT,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit();conn.close()
