from typing import Any, Dict, List

from .base import BaseOntologyService


class VietnameseMappingService(BaseOntologyService):
    """Service for Vietnamese banking domain mappings"""
    
    def __init__(self):
        super().__init__()
        
        # Vietnamese banking mappings
        self.vietnamese_banking_mappings = {
            "FinancialInstrument": {
                "vietnamese_labels": ["công cụ tài chính", "sản phẩm tài chính"],
                "domain": "banking",
            },
            "Account": {"vietnamese_labels": ["tài khoản", "tk"], "domain": "banking"},
            "LegalPerson": {
                "vietnamese_labels": ["pháp nhân", "tổ chức"],
                "domain": "banking",
            },
            "NaturalPerson": {
                "vietnamese_labels": ["cá nhân", "khách hàng cá nhân"],
                "domain": "banking",
            },
            "Bank": {"vietnamese_labels": ["ngân hàng", "nh"], "domain": "banking"},
            "Loan": {"vietnamese_labels": ["khoản vay", "vay"], "domain": "banking"},
            "Deposit": {
                "vietnamese_labels": ["tiền gửi", "gửi tiết kiệm"],
                "domain": "banking",
            },
            "CreditCard": {"vietnamese_labels": ["thẻ tín dụng"], "domain": "banking"},
            "DebitCard": {
                "vietnamese_labels": ["thẻ ghi nợ", "thẻ atm"],
                "domain": "banking",
            },
            "Transaction": {
                "vietnamese_labels": ["giao dịch", "gd"],
                "domain": "banking",
            },
            "Transfer": {
                "vietnamese_labels": ["chuyển khoản", "chuyển tiền"],
                "domain": "banking",
            },
            "InterestRate": {
                "vietnamese_labels": ["lãi suất", "lãi"],
                "domain": "banking",
            },
            "Currency": {
                "vietnamese_labels": ["tiền tệ", "đồng tiền"],
                "domain": "banking",
            },
            "MonetaryAmount": {
                "vietnamese_labels": ["số tiền", "giá trị tiền tệ"],
                "domain": "banking",
            },
        }
        
        # Vietnamese banking relationship mappings
        self.vietnamese_relationship_mappings = {
            "hasAccount": {
                "vietnamese_labels": ["có tài khoản", "sở hữu tài khoản"],
                "domain": "banking",
            },
            "isCustomerOf": {
                "vietnamese_labels": ["là khách hàng của", "giao dịch tại"],
                "domain": "banking",
            },
            "providesService": {
                "vietnamese_labels": ["cung cấp dịch vụ", "phục vụ"],
                "domain": "banking",
            },
            "manages": {
                "vietnamese_labels": ["quản lý", "điều hành"],
                "domain": "banking",
            },
            "transfersTo": {
                "vietnamese_labels": ["chuyển đến", "gửi cho"],
                "domain": "banking",
            },
            "borrowsFrom": {
                "vietnamese_labels": ["vay từ", "đi vay tại"],
                "domain": "banking",
            },
            "depositsIn": {
                "vietnamese_labels": ["gửi vào", "gửi tiết kiệm tại"],
                "domain": "banking",
            },
            "appliesFor": {"vietnamese_labels": ["đăng ký", "mở"], "domain": "banking"},
        }
    
    def add_vietnamese_mappings_to_classes(
        self, 
        classes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Add Vietnamese language mappings to classes"""
        
        for class_info in classes:
            label = class_info.get("label", "")
            
            # Check if we have Vietnamese mappings for this class
            if label in self.vietnamese_banking_mappings:
                mapping = self.vietnamese_banking_mappings[label]
                
                # Add Vietnamese labels to properties
                if "properties" not in class_info:
                    class_info["properties"] = {}
                
                class_info["properties"]["vietnamese_labels"] = mapping["vietnamese_labels"]
                class_info["domain"] = mapping.get("domain", class_info.get("domain"))
                
                # Update description to include Vietnamese context
                if mapping["vietnamese_labels"]:
                    vietnamese_desc = f"Tiếng Việt: {', '.join(mapping['vietnamese_labels'])}"
                    if class_info.get("description"):
                        class_info["description"] += f" ({vietnamese_desc})"
                    else:
                        class_info["description"] = vietnamese_desc
        
        return classes
    
    def add_vietnamese_mappings_to_properties(
        self, 
        properties: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Add Vietnamese language mappings to properties"""
        
        for prop_info in properties:
            label = prop_info.get("label", "")
            
            # Check if we have Vietnamese mappings for this property
            if label in self.vietnamese_relationship_mappings:
                mapping = self.vietnamese_relationship_mappings[label]
                
                # Add Vietnamese labels to description
                if mapping["vietnamese_labels"]:
                    vietnamese_desc = f"Tiếng Việt: {', '.join(mapping['vietnamese_labels'])}"
                    if prop_info.get("description"):
                        prop_info["description"] += f" ({vietnamese_desc})"
                    else:
                        prop_info["description"] = vietnamese_desc
                
                prop_info["domain"] = mapping.get("domain", prop_info.get("domain"))
        
        return properties

