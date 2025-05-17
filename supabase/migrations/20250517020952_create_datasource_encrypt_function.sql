-- Tạo các hàm mã hóa/giải mã để gọi qua REST API
CREATE OR REPLACE FUNCTION encrypt_data_source_credentials(
  p_credentials JSONB,
  p_encryption_key TEXT
) RETURNS BYTEA AS $$
BEGIN
  RETURN pgp_sym_encrypt(p_credentials::TEXT, p_encryption_key);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION decrypt_data_source_credentials(
  p_id UUID,
  p_encryption_key TEXT
) RETURNS JSONB AS $$
DECLARE
  v_result JSONB;
  v_encrypted_data BYTEA;
BEGIN
  -- Chỉ cho phép lấy dữ liệu của user hiện tại
  SELECT encrypted_credentials INTO v_encrypted_data
  FROM data_sources
  WHERE id = p_id AND user_id = auth.uid();
  
  IF v_encrypted_data IS NULL THEN
    RAISE EXCEPTION 'Data source not found or permission denied';
  END IF;
  
  -- Giải mã và trả về JSONB
  v_result := pgp_sym_decrypt(v_encrypted_data, p_encryption_key)::JSONB;
  RETURN v_result;
EXCEPTION
  WHEN OTHERS THEN
    RAISE EXCEPTION 'Decryption failed: %', SQLERRM;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
