# model_backend.py
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

def load_and_process_data(csv_file='BD.csv'):
    df = pd.read_csv(csv_file, encoding='latin1').dropna()
    df['Latitud_round'] = df['Latitud'].round(1)
    df['Longitud_round'] = df['Longitud'].round(1)
    return df

def get_regional_summary_by_year(df, year):
    """Filtra los datos por un año específico y genera el resumen regional."""
    data_year = df[df['Año'] == year]
    if data_year.empty:
        raise ValueError(f"No hay datos para el año {year}")
    # Recalcular coordenadas redondeadas
    data_year['Latitud_round'] = data_year['Latitud'].round(1)
    data_year['Longitud_round'] = data_year['Longitud'].round(1)
    
    region_summary = data_year.groupby(['Latitud_round', 'Longitud_round']).agg(
        frecuencia_incendios=('Año', 'count'),
        duracion_promedio=('Duración días', 'mean'),
        vegetacion_predominante=('Tipo Vegetación', lambda x: x.mode()[0])
    ).reset_index()
    return region_summary

def compute_regional_clusters(region_summary):
    """Aplica KMeans a los datos regionales y añade la asignación de clúster."""
    veg_encoder = OneHotEncoder(sparse_output=False)
    veg_encoded = veg_encoder.fit_transform(region_summary[['vegetacion_predominante']])
    veg_df = pd.DataFrame(veg_encoded, columns=veg_encoder.get_feature_names_out())
    
    region_features = pd.concat([
        region_summary[['frecuencia_incendios', 'duracion_promedio']], veg_df
    ], axis=1)

    scaler = StandardScaler()
    region_scaled = scaler.fit_transform(region_features)

    kmeans_region = KMeans(n_clusters=5, random_state=42, n_init=10)
    region_summary['cluster_region'] = kmeans_region.fit_predict(region_scaled)
    return region_summary

def get_individual_summary_by_year(df, year):
    """Filtra los datos por un año específico y genera el resumen de clústeres individuales."""
    data_year = df[df['Año'] == year]
    if data_year.empty:
        raise ValueError(f"No hay datos para el año {year}")
    data_year = data_year.copy()

    categorical_cols = ['Causa', 'Tipo impacto', 'Tipo Vegetación']
    numerical_cols = ['Duración días', 'Latitud', 'Longitud']

    preprocessor = ColumnTransformer(transformers=[
        ('num', StandardScaler(), numerical_cols),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_cols)
    ])
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('kmeans', KMeans(n_clusters=4, random_state=42, n_init=10))
    ])
    data_year['cluster_incendio'] = pipeline.fit_predict(data_year)

    incendio_profiles = data_year.groupby('cluster_incendio').agg(
        num_incendios=('Año', 'count'),
        duracion_media=('Duración días', 'mean'),
        impacto_comun=('Tipo impacto', lambda x: x.mode()[0]),
        causa_comun=('Causa', lambda x: x.mode()[0]),
        vegetacion_comun=('Tipo Vegetación', lambda x: x.mode()[0])
    ).reset_index()
    return data_year, incendio_profiles

def get_top10_regions_by_year(df, year):
    """Retorna el top 10 de regiones (por frecuencia de incendios) para un año."""
    reg_summary = get_regional_summary_by_year(df, year)
    reg_summary = compute_regional_clusters(reg_summary)
    top10 = reg_summary.sort_values(by='frecuencia_incendios', ascending=False).head(10)
    return top10

def get_ecosystem_summary_by_year(df, year):
    """Retorna el resumen de incendios por ecosistema para un año."""
    data_year = df[df['Año'] == year]
    if data_year.empty:
        raise ValueError(f"No hay datos para el año {year}")
    ecosistema_summary = data_year.groupby('Tipo Vegetación').agg(
        frecuencia_incendios=('Año', 'count'),
        duracion_promedio=('Duración días', 'mean')
    ).sort_values(by='frecuencia_incendios', ascending=False).reset_index()
    return ecosistema_summary

def compute_risk_matrix_by_year(df, year):
    """
    Para un año, asigna a cada incidente el clúster regional (según sus coordenadas redondeadas)
    y cruza con el clúster individual para generar la matriz de riesgo.
    """
    # Filtrar el dataframe para el año indicado
    data_year = df[df['Año'] == year].copy()
    if data_year.empty:
        raise ValueError(f"No hay datos para el año {year}")
    
    # Calcular el resumen regional usando el subconjunto filtrado
    reg_summary = get_regional_summary_by_year(data_year, year)
    reg_summary = compute_regional_clusters(reg_summary)
    
    # Asignar a cada incidente su clúster regional mediante merge
    data_year = data_year.merge(reg_summary[['Latitud_round','Longitud_round','cluster_region']], 
                                on=['Latitud_round','Longitud_round'], how='left')
    
    # Calcular el clúster individual utilizando también el subconjunto filtrado
    data_year_ind, _ = get_individual_summary_by_year(data_year, year)
    
    # Generar la matriz de riesgo cruzando ambos clústeres
    risk_matrix = pd.crosstab(data_year['cluster_region'], data_year_ind['cluster_incendio'])
    return risk_matrix

def get_top10_regions_historical(csv_file='BD.csv'):
    """Retorna el top 10 de regiones usando datos históricos (2015-2023)."""
    df = load_and_process_data(csv_file)
    df_hist = df[(df['Año'] >= 2015) & (df['Año'] <= 2023)].copy()
    reg_summary = df_hist.groupby(['Latitud_round', 'Longitud_round']).agg(
        frecuencia_incendios=('Año', 'count'),
        duracion_promedio=('Duración días', 'mean'),
        vegetacion_predominante=('Tipo Vegetación', lambda x: x.mode()[0])
    ).reset_index()
    reg_summary = compute_regional_clusters(reg_summary)
    top10 = reg_summary.sort_values(by='frecuencia_incendios', ascending=False).head(10)
    return top10

def get_ecosystem_summary_historical(csv_file='BD.csv'):
    """Retorna el resumen de ecosistemas usando datos históricos (2015-2023)."""
    df = load_and_process_data(csv_file)
    df_hist = df[(df['Año'] >= 2015) & (df['Año'] <= 2023)].copy()
    ecosistema_summary = df_hist.groupby('Tipo Vegetación').agg(
        frecuencia_incendios=('Año', 'count'),
        duracion_promedio=('Duración días', 'mean')
    ).sort_values(by='frecuencia_incendios', ascending=False).reset_index()
    return ecosistema_summary

def compute_risk_matrix_historical(csv_file='BD.csv'):
    """Genera la matriz de riesgo usando todos los datos de 2015 a 2023."""
    df = load_and_process_data(csv_file)
    df_hist = df[(df['Año'] >= 2015) & (df['Año'] <= 2023)].copy()
    # Regional
    reg_summary = df_hist.groupby(['Latitud_round', 'Longitud_round']).agg(
        frecuencia_incendios=('Año', 'count'),
        duracion_promedio=('Duración días', 'mean'),
        vegetacion_predominante=('Tipo Vegetación', lambda x: x.mode()[0])
    ).reset_index()
    reg_summary = compute_regional_clusters(reg_summary)
    df_hist = df_hist.merge(reg_summary[['Latitud_round','Longitud_round','cluster_region']], 
                            on=['Latitud_round','Longitud_round'], how='left')
    # Individual: calcular clúster individual para los datos históricos
    categorical_cols = ['Causa', 'Tipo impacto', 'Tipo Vegetación']
    numerical_cols = ['Duración días', 'Latitud', 'Longitud']
    preprocessor = ColumnTransformer(transformers=[
        ('num', StandardScaler(), numerical_cols),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_cols)
    ])
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('kmeans', KMeans(n_clusters=4, random_state=42, n_init=10))
    ])
    df_hist['cluster_incendio'] = pipeline.fit_predict(df_hist)
    risk_matrix = pd.crosstab(df_hist['cluster_region'], df_hist['cluster_incendio'])
    return risk_matrix

def historical_analysis(csv_file='BD.csv'):
    """
    Realiza el análisis histórico utilizando la información acumulada de 2015 a 2023.
    Retorna:
      - Resumen regional (con clústeres)
      - Resumen individual (agrupado por clúster)
      - Top 10 regiones
      - Resumen de ecosistemas
      - Matriz de riesgo
    """
    df = load_and_process_data(csv_file)
    df_hist = df[(df['Año'] >= 2015) & (df['Año'] <= 2023)].copy()
    
    # Regional
    reg_summary = df_hist.groupby(['Latitud_round', 'Longitud_round']).agg(
        frecuencia_incendios=('Año', 'count'),
        duracion_promedio=('Duración días', 'mean'),
        vegetacion_predominante=('Tipo Vegetación', lambda x: x.mode()[0])
    ).reset_index()
    reg_summary = compute_regional_clusters(reg_summary)
    
    # Top 10 regiones
    top10 = reg_summary.sort_values(by='frecuencia_incendios', ascending=False).head(10)
    
    # Ecosistema
    ecosistema_summary = df_hist.groupby('Tipo Vegetación').agg(
        frecuencia_incendios=('Año', 'count'),
        duracion_promedio=('Duración días', 'mean')
    ).sort_values(by='frecuencia_incendios', ascending=False).reset_index()
    
    # Individual: calcular clúster individual para los datos históricos
    categorical_cols = ['Causa', 'Tipo impacto', 'Tipo Vegetación']
    numerical_cols = ['Duración días', 'Latitud', 'Longitud']
    preprocessor = ColumnTransformer(transformers=[
        ('num', StandardScaler(), numerical_cols),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_cols)
    ])
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('kmeans', KMeans(n_clusters=4, random_state=42, n_init=10))
    ])
    df_hist['cluster_incendio'] = pipeline.fit_predict(df_hist)
    ind_summary = df_hist.groupby('cluster_incendio').agg(
        num_incendios=('Año', 'count'),
        duracion_media=('Duración días', 'mean'),
        impacto_comun=('Tipo impacto', lambda x: x.mode()[0]),
        causa_comun=('Causa', lambda x: x.mode()[0]),
        vegetacion_comun=('Tipo Vegetación', lambda x: x.mode()[0])
    ).reset_index()
    
    # Matriz de riesgo histórica
    risk_matrix = compute_risk_matrix_historical(csv_file)
    
    return {
        'regional': reg_summary,
        'individual': {'data': df_hist, 'summary': ind_summary},
        'top10_regiones': top10,
        'ecosistema_summary': ecosistema_summary,
        'risk_matrix': risk_matrix
    }

if __name__ == "__main__":
    # Ejemplo de uso de análisis histórico
    results = historical_analysis()
    print("Análisis histórico completado (2015-2023).")
    print("Top 10 Regiones:")
    print(results['top10_regiones'][['Latitud_round', 'Longitud_round', 'frecuencia_incendios', 'vegetacion_predominante']])
    print("\nResumen Ecosistemas:")
    print(results['ecosistema_summary'].head())
    print("\nMatriz de Riesgo:")
    print(results['risk_matrix'])
