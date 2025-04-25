import streamlit as st
import pandas as pd
from io import StringIO

def main():
    st.title("CSV Type and Hours Assignment")
    
    # File upload
    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
    
    if uploaded_file is not None:
        # Read CSV file
        try:
            df = pd.read_csv(uploaded_file)
            
            # Check if required columns exist
            if 'Type' not in df.columns or 'Name' not in df.columns:
                st.error("CSV file must contain 'Type' and 'Name' columns")
                return
            
            # Filter out rows with empty Type or Name
            df = df.dropna(subset=['Type', 'Name'])
            df = df[df['Type'].astype(str).str.strip() != '']
            df = df[df['Name'].astype(str).str.strip() != '']
            
            # Reset index after filtering
            df.reset_index(drop=True, inplace=True)
            
            # Initialize hours column if not exists
            if 'Hours' not in df.columns:
                df['Hours'] = 0
            
            st.subheader("Uploaded Data Preview")
            st.dataframe(df.head())
            
            # Get unique types
            unique_types = df['Type'].unique()
            
            st.subheader("Assign Hours by Type")
            
            # Create a dictionary to store hours per type
            type_hours = {}
            for type_val in unique_types:
                type_hours[type_val] = st.number_input(
                    f"Hours for '{type_val}'",
                    min_value=0.0,
                    value=0.0,
                    step=0.5,
                    key=f"type_{type_val}"
                )
            
            st.subheader("Assign Specific Hours by Keyword in Name")
            
            # Keyword hours assignment
            keyword_hours = {}
            col1, col2 = st.columns(2)
            
            with col1:
                keyword = st.text_input("Keyword to search in Name column")
            with col2:
                hours = st.number_input(
                    "Hours for rows containing keyword",
                    min_value=0.0,
                    value=0.0,
                    step=0.5,
                    key="keyword_hours"
                )
            
            if keyword and hours > 0:
                keyword_hours[keyword] = hours
            
            # Apply the hours assignments
            if st.button("Apply Hours Assignment"):
                # First apply type-based hours
                for type_val, hours in type_hours.items():
                    df.loc[df['Type'] == type_val, 'Hours'] = hours
                
                # Then override with keyword-based hours if applicable
                for keyword, hours in keyword_hours.items():
                    df.loc[df['Name'].str.contains(keyword, case=False, na=False), 'Hours'] = hours
                
                st.success("Hours assigned successfully!")
                
                # Show updated dataframe
                st.subheader("Updated Data")
                st.dataframe(df)
                
                # Download button
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download CSV with Hours",
                    data=csv,
                    file_name='data_with_hours.csv',
                    mime='text/csv'
                )
                
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    main()