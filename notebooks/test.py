import pandas as pd
from sentence_transformers import SentenceTransformer, models
from sentence_transformers import InputExample
from torch.utils.data import DataLoader
from sentence_transformers import losses
from torch.nn.functional import cosine_similarity
from itertools import islice


def get_experience(exp_str: str) -> str:
    exp_lst = exp_str.split()
    if len(exp_lst) <= 2:
        return 0
    if 'лет' not in ' '.join(exp_lst[:5]) and 'год' not in ' '.join(exp_lst[:5]):
        return int(exp_lst[2]) / 12
    if 'месяц' in ' '.join(exp_lst[:5]):
        return int(exp_lst[2]) + int(exp_lst[4]) / 12
    else:
        return int(exp_lst[2])


def get_education(edu_list: list) -> str:
    final = list()
    for word in edu_list:
        if not word.isalpha():
            break
            
        final.append(word)
        
    return ' '.join(final)


def get_resume_data():
    df_resume = pd.read_csv('dst-3.0_16_1_hh_database.csv', delimiter=';')
    df_resume['Ищет работу на должность:'] = df_resume['Ищет работу на должность:'].str.split(', ')
    df_resume = df_resume.explode('Ищет работу на должность:')
    df_resume['Ищет работу на должность:'] = df_resume['Ищет работу на должность:'].str.lower()
    df_resume = df_resume.reset_index()
    df_resume = df_resume.dropna()
    df_resume['years'] = df_resume['Опыт работы'].apply(lambda x: get_experience(x))
    df_resume['city'] = df_resume['Город, переезд, командировки'].str.split(',').apply(lambda x: x[0])
    df_resume['education'] = df_resume['Образование и ВУЗ'].str.split().apply(get_education)
    
    return df_resume


def get_vac_data():
    df_it_vacancies = pd.read_csv('IT_vacancies_full.csv')
    df_it_vacancies['min_years'] = df_it_vacancies['Experience'].replace({
                                                                            'От 3 до 6 лет': 3, 
                                                                            'От 1 года до 3 лет': 1,
                                                                            'Нет опыта': 0,
                                                                            'Более 6 лет': 6
                                                                        })
    df_it_vacancies['Name'] = df_it_vacancies['Name'].str.lower()
    df_it_vacancies['Name'] = df_it_vacancies['Name'].str.split('/').apply(lambda x: x[0])

    return df_it_vacancies


def get_merged_data():
    df_it_vacancies, df_resume = get_vac_data(), get_resume_data()

    job_resume = df_it_vacancies.merge(df_resume, left_on='Name', right_on='Ищет работу на должность:', how='left')
    job_resume = job_resume.dropna(subset=['Ищет работу на должность:'])
    job_resume = job_resume.drop_duplicates(subset=['Ids', 'index'])

    counts = job_resume['Ids'].value_counts()
    counts = counts[counts >= 10]
    to_keep = counts.index
    job_resume = job_resume[job_resume['Ids'].isin(to_keep)]
    job_resume = job_resume[job_resume['years'] >= job_resume['min_years']]
    job_resume = job_resume[(job_resume['city']==job_resume['Area'])|(job_resume['Schedule']=='Удаленная работа')]

    job_resume['Description'] = job_resume['Description'].astype(str)
    job_resume['Опыт работы'] = job_resume['Опыт работы'].astype(str)

    return job_resume


if __name__ == "__main__":
    job_resume = get_merged_data()

    model = SentenceTransformer("all-MiniLM-L6-v2")

    train_examples = []

    for _, row in islice(job_resume.iterrows(), 100_000):
        train_examples.append(InputExample(texts=[row["Description"], row["Опыт работы"]]))

    print(len(train_examples))

    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=32)
    train_loss = losses.MultipleNegativesRankingLoss(model=model)

    num_epochs = 3
    warmup_steps = int(len(train_dataloader) * num_epochs * 0.1) #10% of train data

    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=num_epochs,
        warmup_steps=warmup_steps,
    )

    r = model.encode(["Имею опыт работы по машинному обучению, работал на PyTorch и Tensorflow", "Требуется пекарь в местную булочную", "Ищем хорошего специалиста по ML, приветствуется опыт с современными фреймворками"], convert_to_tensor=True)
    print(r)
    print(r.shape)
    print(cosine_similarity(r[0].unsqueeze(0), r[1].unsqueeze(0)))
    print(cosine_similarity(r[0].unsqueeze(0), r[2].unsqueeze(0)))
