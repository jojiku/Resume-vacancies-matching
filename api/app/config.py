path_to_res_index = (
    "init_data/flat_res.index"
)
path_to_vac_index = (
    "init_data/flat_vac.index"
)
topn = 10

path_to_res = "init_data/resume_train_no_index.csv"
res_faiss_func = (
    lambda x: f"Ищет работу на должность: {x['job_title']}; {x['experience']}; {x['edu']}"
)

path_to_vac = "init_data/vac_train_no_index.csv"
vac_faiss_func = (
    lambda x: f"{x['descr']}; {x['key_req']}; {x['spec']}. Требуемый опыт: {x['req_exp']}"
)

healthcheck_timeout = 30
healthcheck_sleep = 5

min_max_lens = {
    "job_title": (5, 30),
    "experience": (20, 2000),
    "edu": (3, 100),
    "employer": (2, 100),
    "req_exp": (3, 100),
    "descr": (50, 2000),
    "key_req": (10, 500),
    "spec": (10, 500),
}
min_len, max_len = 0, 1000
