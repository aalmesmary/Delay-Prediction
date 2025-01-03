import pandas as pd
from sklearn.preprocessing import LabelEncoder
import streamlit as st
import pickle
import os

# Load the pre-trained model and scaler
@st.cache_resource
def load_resources():
    with open(
        os.path.join(os.getcwd(), "Models", "Delay_Status_model.pkl"), "rb"
    ) as model_file, open(
        os.path.join(os.getcwd(), "Models", "scaler.pkl"), "rb"
    ) as scaler_file:
        model = pickle.load(model_file)
        scaler = pickle.load(scaler_file)
    return model, scaler


def prediction(sample_data: pd.DataFrame) -> pd.DataFrame:
    # Load the datasets
    tasks_df = pd.read_excel(os.path.join(os.getcwd(), 'data', 'raw', 'P2543-R01-Oct24. Rel.xlsx'), sheet_name="TASK")
    taskspred_df = pd.read_excel(os.path.join(os.getcwd(), 'data', 'raw', 'P2543-R01-Oct24. Rel.xlsx'), sheet_name="TASKPRED")
    
    #remove spaces
    sample_data['Activity ID']=sample_data['Activity ID'].str.strip()
    tasks_df['task_code']=tasks_df['task_code'].str.strip()
    taskspred_df['task_id']=taskspred_df['task_id'].str.strip()
    
    merged_df = pd.merge(sample_data, tasks_df, how='left', left_on='Activity ID', right_on='task_code')
    merged_df = pd.merge(merged_df, taskspred_df, how='left', left_on='Activity ID', right_on='task_id')
    
    # Parse date fields
    date_columns = ['Baseline Start', 'Baseline Finish', 'Start', 'Finish', 'start_date', 'end_date']
    for col in date_columns:
        if col in merged_df.columns:
            merged_df[col] = pd.to_datetime(merged_df[col], errors='coerce',format="yyyy-mm-dd")
    
    
    # Calculate delay duration
    merged_df['Delay_Duration'] = (merged_df['Finish'] - merged_df['Baseline Finish']).dt.days
    merged_df['Delay_Status'] = merged_df['Delay_Duration'].apply(lambda x: 1 if x > 0 else 0)
    
    # Feature engineering: Count predecessors/successors
    merged_df['Predecessor_Count'] = merged_df['pred_list'].apply(lambda x: len(x.split(',')) if pd.notna(x) else 0)
    merged_df['Successor_Count'] = merged_df['succ_list'].apply(lambda x: len(x.split(',')) if pd.notna(x) else 0)
    
    merged_df=merged_df.dropna(subset=['task_code'])
    
    # Handle missing data
    merged_df.fillna({
        'Original Duration': 0,
        'Remaining Duration': 0,
        'Total Float': 0
    }, inplace=True)
    
    
    # Encode categorical variables
    label_encoders = {}
    for col in ['status_code']:
        if col in merged_df.columns:
            le = LabelEncoder()
            merged_df[col] = le.fit_transform(merged_df[col])
            label_encoders[col] = le
    
    columns_to_drop = [
    "task_name", "pred_details", "succ_details",
    "predtask__projwbs__wbs_full_name", "task__projwbs__wbs_full_name",
    "predtask__task_name", "task__task_name", "task_code", "task_id","wbs_id",'lag_hr_cnt'
    ]

    merged_df.drop(columns=[col for col in columns_to_drop if col in merged_df.columns], inplace=True)
    
    # Convert datetime columns if not already converted
    date_columns = ['Baseline Start', 'Baseline Finish', 'Start', 'Finish', 'start_date', 'end_date']
    for col in date_columns:
        if col in merged_df.columns:
            merged_df[col] = pd.to_datetime(merged_df[col])
    
    model, scaler = load_resources()
    
    # scale numerical values
    numerical_cols=['Original Duration', 'Remaining Duration', 'Total Float','Predecessor_Count','Successor_Count', 'Delay_Duration']
    merged_df[numerical_cols] = scaler.transform(merged_df[numerical_cols])
    
    input_data = merged_df[['Original Duration', 'Remaining Duration', 'Total Float','Predecessor_Count','Successor_Count']]
    
    prediction = model.predict(input_data)
    
    merged_df['Predicted_Delay_Status'] = ["Delayed" if x > 0.50 else "On Time" for x in prediction]
    
    return merged_df[['Activity ID', "Activity Name",'Predicted_Delay_Status']].drop_duplicates().reset_index(drop=True)


if __name__ == "__main__":
    # print(os.path.join(os.getcwd(), 'data', 'sample_data.csv'))
    print(prediction(pd.read_csv(os.path.join(os.getcwd(), 'data', 'sample.csv'))))