import streamlit as st
import pandas as pd
from thefuzz import process, fuzz
from io import StringIO
import chardet
import uuid

# Algorithm options with descriptions
MATCH_ALGORITHMS = {
    "Ratio": fuzz.ratio,
    "Partial Ratio": fuzz.partial_ratio,
    "Token Sort": fuzz.token_sort_ratio,
    "Token Set": fuzz.token_set_ratio,
    "WRatio": fuzz.WRatio
}

def detect_encoding(file):
    """Detect file encoding using chardet"""
    rawdata = file.read()
    result = chardet.detect(rawdata)
    file.seek(0)  # Reset file pointer
    return result['encoding']

def read_csv(file):
    """Read CSV with automatic encoding detection"""
    encoding = detect_encoding(file)
    try:
        return pd.read_csv(file, encoding=encoding)
    except UnicodeDecodeError:
        file.seek(0)
        try:
            return pd.read_csv(file, encoding='utf-16')
        except:
            file.seek(0)
            return pd.read_csv(file, encoding='latin1')  # Fallback

def fill_missing_values(df1, df2, match_col1, match_col2, data_col2, threshold=80, algorithm="Token Set", prevent_duplicates=True):
    """Fill missing values using fuzzy matching on selected columns"""
    filled_df = df1[[match_col1]].copy()  # Start with only the matching column
    scorer = MATCH_ALGORITHMS[algorithm]
    
    # Add result columns
    filled_df['Filled Data'] = None
    filled_df['Match Score'] = 0
    filled_df['Matched Name'] = ""
    filled_df['Algorithm Used'] = algorithm
    
    # Create dictionary from df2 using selected matching and data columns
    df2_dict = dict(zip(
        df2[match_col2],
        df2[data_col2]
    ))
    
    used_matches = set() if prevent_duplicates else None
    
    for index, row in filled_df.iterrows():
        if pd.isna(row.get('Filled Data', True)):  # Check if data needs filling
            available_matches = {k:v for k,v in df2_dict.items() 
                               if not prevent_duplicates or k not in used_matches}
            
            if not available_matches:
                continue
                
            best_match = process.extractOne(
                row[match_col1],
                available_matches.keys(),
                scorer=scorer
            )
            
            if best_match and best_match[1] >= threshold:
                match_name, match_score = best_match[0], best_match[1]
                filled_df.at[index, 'Filled Data'] = df2_dict[match_name]
                filled_df.at[index, 'Match Score'] = match_score
                filled_df.at[index, 'Matched Name'] = match_name
                
                if prevent_duplicates:
                    used_matches.add(match_name)
    
    return filled_df

def main():
    st.title("🔍 Flexible CSV Value Matcher (UTF-16 Supported)")
    st.markdown("Fill missing values by matching selected columns between CSV files")
    
    col1, col2 = st.columns(2)
    with col1:
        uploaded_file1 = st.file_uploader(
            "File with missing values", 
            type="csv",
            help="Supports UTF-8, UTF-16, and other encodings"
        )
    with col2:
        uploaded_file2 = st.file_uploader(
            "Reference file with complete values", 
            type="csv"
        )
    
    if uploaded_file1 and uploaded_file2:
        # Read files with encoding detection
        df1 = read_csv(uploaded_file1)
        df2 = read_csv(uploaded_file2)
        
        with st.expander("Column Selection and Matching Settings", expanded=True):
            # Column selection for first file
            match_col1 = st.selectbox(
                "Select column to match from first file",
                options=df1.columns,
                key="match_col1"
            )
            
            # Column selection for second file
            match_col2 = st.selectbox(
                "Select column to match from second file",
                options=df2.columns,
                key="match_col2"
            )
            
            data_col2 = st.selectbox(
                "Select column with data to fill from second file",
                options=df2.columns,
                key="data_col2"
            )
            
            # Matching settings
            algorithm = st.selectbox(
                "Matching Algorithm",
                options=list(MATCH_ALGORITHMS.keys()),
                index=3
            )
            
            threshold = st.slider(
                "Minimum Match Score",
                min_value=0, max_value=100, value=80
            )
            
            prevent_duplicates = st.checkbox(
                "Prevent duplicate use of reference values",
                value=True
            )
            
            output_encoding = st.selectbox(
                "Output file encoding",
                options=['utf-8', 'utf-16'],
                index=0
            )
        
        try:
            # Clean data for selected columns
            df1[match_col1] = df1[match_col1].astype(str).str.lower().str.strip()
            df2[match_col2] = df2[match_col2].astype(str).str.lower().str.strip()
            
            # Process data
            with st.spinner("Matching projects..."):
                result_df = fill_missing_values(
                    df1, df2,
                    match_col1=match_col1,
                    match_col2=match_col2,
                    data_col2=data_col2,
                    threshold=threshold,
                    algorithm=algorithm,
                    prevent_duplicates=prevent_duplicates
                )
            
            st.success(f"Completed! Filled {result_df['Match Score'].gt(0).sum()} values")
            
            tab1, tab2 = st.tabs(["All Data", "Filled Values"])
            with tab1:
                st.dataframe(result_df)
            with tab2:
                st.dataframe(result_df[result_df['Match Score'] > 0])
            
            # Download with selected encoding
            csv = result_df.to_csv(index=False)
            if output_encoding == 'utf-16':
                csv = csv.encode('utf-16')
            st.download_button(
                "Download Results",
                data=csv,
                file_name=f"filled_results_{output_encoding}.csv",
                mime="text/csv"
            )
            
        except Exception as e:
            st.error(f"Error processing files: {str(e)}")

if __name__ == "__main__":
    main()
