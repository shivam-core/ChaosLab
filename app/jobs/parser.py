import io
import pandas as pd
from datetime import datetime, timezone
import hashlib
import json
from sqlalchemy.orm import Session
from app.models.domain import Upload, Dataset, Transaction

def process_parse_job(session: Session, upload_id: str):
    upload = session.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise Exception("Upload not found")
        
    try:
        # Load into pandas
        content = upload.raw_bytes
        if upload.original_name.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
            
        # Map columns
        # Assume columns are roughly: date, product, quantity, unit_price
        # Will handle basic mapping
        col_map = {}
        for col in df.columns:
            lower = col.lower()
            if 'date' in lower:
                col_map[col] = 'transaction_date'
            elif 'prod' in lower or 'item' in lower:
                col_map[col] = 'product_id'
            elif 'qty' in lower or 'quant' in lower:
                col_map[col] = 'quantity'
            elif 'price' in lower or 'cost' in lower:
                col_map[col] = 'unit_price'
            elif 'order' in lower:
                col_map[col] = 'order_id'
                
        df = df.rename(columns=col_map)
        
        # Require essential columns
        if 'transaction_date' not in df.columns or 'quantity' not in df.columns or 'product_id' not in df.columns:
            raise Exception("Missing required columns: date, quantity, product")
            
        df['transaction_date'] = pd.to_datetime(df['transaction_date'], utc=True)
        df['quantity'] = pd.to_numeric(df['quantity']).fillna(0).astype(int)
        
        coverage_start = df['transaction_date'].min().to_pydatetime()
        coverage_end = df['transaction_date'].max().to_pydatetime()
        
        # Create Dataset
        dataset = Dataset(
            workspace_id=upload.workspace_id,
            name=f"Dataset from {upload.original_name}",
            currency="USD",
            coverage_start=coverage_start,
            coverage_end=coverage_end,
            dataset_hash=upload.sha256_hash,
            summary={"rows": len(df)}
        )
        session.add(dataset)
        session.flush()
        
        # Create Transactions
        transactions = []
        for i, row in df.iterrows():
            t = Transaction(
                dataset_id=dataset.id,
                source_row_id=str(i),
                transaction_date=row['transaction_date'],
                product_id=str(row['product_id']),
                quantity=row['quantity'],
                unit_price_minor=int(row.get('unit_price', 0) * 100) if 'unit_price' in row else None,
                order_id=str(row.get('order_id', '')) if 'order_id' in row else None,
                provenance={}
            )
            transactions.append(t)
            
        session.bulk_save_objects(transactions)
        
        upload.status = "ready"
        session.commit()
        
    except Exception as e:
        upload.status = "rejected"
        session.commit()
        raise e
