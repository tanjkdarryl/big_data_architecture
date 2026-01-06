"""
Data Validator Module - Implementing VERACITY in the 5Vs Framework

=== VERACITY: THE FOURTH V OF BIG DATA ===

Veracity refers to the quality, accuracy, and trustworthiness of data. In big data
systems, bad data can lead to bad decisions. This module implements data quality
checks to ensure the blockchain data we collect is reliable.

Why Veracity Matters in Blockchain Data:
1. API Errors: External APIs may return malformed or incomplete data
2. Network Issues: Timeouts can cause partial data retrieval
3. Chain Reorganizations: Blocks can be orphaned and replaced
4. Timestamp Drift: Node clocks may be slightly off
5. Data Gaps: Missed blocks or transactions during collection

This module provides:
- Schema validation: Ensuring required fields exist and have correct types
- Range validation: Checking values are within expected bounds
- Temporal validation: Verifying timestamps are reasonable
- Consistency checks: Cross-referencing related data
- Anomaly detection: Flagging unusual patterns

Quality Dimensions Measured:
┌────────────────┬────────────────────────────────────────────────────────────┐
│ Completeness   │ Are all required fields present and non-null?             │
│ Accuracy       │ Are values within expected ranges?                        │
│ Consistency    │ Do related fields agree? (e.g., tx_count matches txs)     │
│ Timeliness     │ Is the timestamp recent and reasonable?                   │
│ Validity       │ Does the data conform to expected formats?                │
└────────────────┴────────────────────────────────────────────────────────────┘
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class QualityLevel(Enum):
    """
    Data quality classification levels.

    HIGH: Data passes all validation checks
    MEDIUM: Minor issues detected but data is usable
    LOW: Significant issues that may affect analysis
    INVALID: Data fails critical validation and should be rejected
    """
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INVALID = "invalid"


@dataclass
class ValidationResult:
    """
    Result of a data validation check.

    Attributes:
        is_valid: Whether the data passed validation
        quality_level: Overall quality classification
        issues: List of detected issues (empty if valid)
        warnings: Non-critical observations
        metrics: Quantitative quality metrics
    """
    is_valid: bool
    quality_level: QualityLevel
    issues: List[str]
    warnings: List[str]
    metrics: Dict[str, float]


class DataValidator:
    """
    Validates blockchain data for quality and consistency.

    === 5Vs CONNECTION: VERACITY ===

    This class is the primary implementation of Veracity in our pipeline.
    It ensures that the high Volume of data flowing through at high Velocity
    from various sources (Variety) maintains sufficient quality for
    extracting Value.

    Usage:
        validator = DataValidator()
        result = validator.validate_bitcoin_block(block_data)
        if not result.is_valid:
            logger.warning(f"Quality issues: {result.issues}")
    """

    # Expected ranges for Bitcoin data (based on protocol rules and observations)
    BITCOIN_BLOCK_SIZE_MAX = 4_000_000  # 4MB max weight
    BITCOIN_TX_PER_BLOCK_MAX = 10_000   # Typical max transactions
    BITCOIN_DIFFICULTY_MIN = 1          # Genesis difficulty
    BITCOIN_TIMESTAMP_TOLERANCE_HOURS = 2  # Bitcoin allows 2 hour drift

    # Expected ranges for Solana data
    SOLANA_SLOT_TIME_MS = 400           # ~400ms per slot
    SOLANA_TX_PER_BLOCK_MAX = 50_000    # High throughput chain
    SOLANA_FEE_MIN_LAMPORTS = 5000      # Minimum fee (5000 lamports)
    SOLANA_TIMESTAMP_TOLERANCE_SECONDS = 60  # Tighter tolerance

    def __init__(self):
        """Initialize the validator with tracking for quality metrics."""
        self.validation_counts = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0
        }

    def validate_bitcoin_block(self, block_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate a Bitcoin block for data quality.

        VERACITY CHECKS PERFORMED:
        1. Completeness: All required fields present
        2. Accuracy: Values within expected protocol ranges
        3. Temporal validity: Timestamp is reasonable
        4. Hash format: Block hash follows expected pattern

        Args:
            block_data: Dictionary containing Bitcoin block fields

        Returns:
            ValidationResult with quality assessment
        """
        issues = []
        warnings = []
        metrics = {}

        # === COMPLETENESS CHECK ===
        # Verify all required fields are present
        required_fields = [
            'block_height', 'block_hash', 'timestamp', 'previous_block_hash',
            'merkle_root', 'difficulty', 'nonce', 'size', 'weight', 'transaction_count'
        ]

        missing_fields = [f for f in required_fields if f not in block_data or block_data[f] is None]
        if missing_fields:
            issues.append(f"Missing required fields: {missing_fields}")

        completeness_score = (len(required_fields) - len(missing_fields)) / len(required_fields)
        metrics['completeness'] = completeness_score

        # === ACCURACY CHECKS ===
        # Block height must be non-negative
        if block_data.get('block_height', -1) < 0:
            issues.append(f"Invalid block_height: {block_data.get('block_height')}")

        # Size and weight must be positive and within limits
        size = block_data.get('size', 0)
        weight = block_data.get('weight', 0)

        if size <= 0:
            issues.append(f"Invalid block size: {size}")
        elif size > self.BITCOIN_BLOCK_SIZE_MAX:
            warnings.append(f"Unusually large block size: {size} bytes")

        if weight <= 0:
            issues.append(f"Invalid block weight: {weight}")
        elif weight > self.BITCOIN_BLOCK_SIZE_MAX:
            warnings.append(f"Block weight exceeds expected max: {weight}")

        # Difficulty must be positive
        difficulty = block_data.get('difficulty', 0)
        if difficulty < self.BITCOIN_DIFFICULTY_MIN:
            issues.append(f"Invalid difficulty: {difficulty}")

        # Transaction count sanity check
        tx_count = block_data.get('transaction_count', 0)
        if tx_count < 1:
            warnings.append(f"Block has no transactions (coinbase missing?): {tx_count}")
        elif tx_count > self.BITCOIN_TX_PER_BLOCK_MAX:
            warnings.append(f"Unusually high transaction count: {tx_count}")

        metrics['tx_count'] = tx_count

        # === TEMPORAL VALIDITY ===
        # Timestamp should be within reasonable range
        timestamp = block_data.get('timestamp')
        if timestamp:
            now = datetime.now()
            time_diff = abs((now - timestamp).total_seconds() / 3600)  # Hours

            if timestamp > now + timedelta(hours=self.BITCOIN_TIMESTAMP_TOLERANCE_HOURS):
                issues.append(f"Block timestamp is in the future: {timestamp}")
            elif time_diff > 24 * 365:  # More than a year old
                warnings.append(f"Block is very old: {timestamp}")

            metrics['timestamp_age_hours'] = time_diff
        else:
            issues.append("Missing timestamp")

        # === HASH FORMAT VALIDATION ===
        # Bitcoin hashes are 64 hex characters (256 bits)
        block_hash = block_data.get('block_hash', '')
        if not self._is_valid_hash(block_hash, 64):
            issues.append(f"Invalid block_hash format: {block_hash[:20]}...")

        merkle_root = block_data.get('merkle_root', '')
        if not self._is_valid_hash(merkle_root, 64):
            warnings.append(f"Invalid merkle_root format")

        # === CALCULATE OVERALL QUALITY ===
        self.validation_counts['total'] += 1

        if issues:
            self.validation_counts['failed'] += 1
            quality_level = QualityLevel.INVALID if len(issues) > 2 else QualityLevel.LOW
        elif warnings:
            self.validation_counts['warnings'] += 1
            quality_level = QualityLevel.MEDIUM
        else:
            self.validation_counts['passed'] += 1
            quality_level = QualityLevel.HIGH

        metrics['quality_score'] = self._calculate_quality_score(issues, warnings)

        return ValidationResult(
            is_valid=len(issues) == 0,
            quality_level=quality_level,
            issues=issues,
            warnings=warnings,
            metrics=metrics
        )

    def validate_bitcoin_transaction(self, tx_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate a Bitcoin transaction for data quality.

        VERACITY CHECKS:
        1. Required fields present (tx_hash, fee, inputs, outputs)
        2. Fee is non-negative (can be 0 for coinbase)
        3. Input/output counts are positive
        4. Size and weight are reasonable
        """
        issues = []
        warnings = []
        metrics = {}

        # Completeness check
        required_fields = ['tx_hash', 'block_height', 'fee', 'input_count', 'output_count']
        missing = [f for f in required_fields if f not in tx_data or tx_data[f] is None]
        if missing:
            issues.append(f"Missing fields: {missing}")

        metrics['completeness'] = (len(required_fields) - len(missing)) / len(required_fields)

        # Fee validation (can be 0 for coinbase transaction)
        fee = tx_data.get('fee', -1)
        if fee < 0:
            issues.append(f"Negative fee: {fee}")
        elif fee == 0:
            warnings.append("Zero fee (coinbase transaction?)")

        # Input/output counts
        input_count = tx_data.get('input_count', 0)
        output_count = tx_data.get('output_count', 0)

        if input_count == 0 and output_count > 0:
            # Coinbase transaction has no inputs
            warnings.append("No inputs (coinbase transaction)")
        elif input_count < 0 or output_count < 0:
            issues.append(f"Invalid input/output counts: {input_count}/{output_count}")

        if output_count == 0:
            issues.append("Transaction has no outputs")

        # Hash format
        tx_hash = tx_data.get('tx_hash', '')
        if not self._is_valid_hash(tx_hash, 64):
            issues.append(f"Invalid tx_hash format")

        # Calculate quality
        quality_level = self._determine_quality_level(issues, warnings)
        metrics['quality_score'] = self._calculate_quality_score(issues, warnings)

        return ValidationResult(
            is_valid=len(issues) == 0,
            quality_level=quality_level,
            issues=issues,
            warnings=warnings,
            metrics=metrics
        )

    def validate_solana_block(self, block_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate a Solana block for data quality.

        VERACITY CHECKS:
        1. Slot and block_height consistency (block_height <= slot)
        2. Timestamp is reasonable
        3. Parent slot is less than current slot
        4. Transaction count within expected range
        """
        issues = []
        warnings = []
        metrics = {}

        # Completeness
        required_fields = ['slot', 'block_height', 'block_hash', 'timestamp',
                          'parent_slot', 'transaction_count']
        missing = [f for f in required_fields if f not in block_data or block_data[f] is None]
        if missing:
            issues.append(f"Missing fields: {missing}")

        metrics['completeness'] = (len(required_fields) - len(missing)) / len(required_fields)

        # Slot/height consistency
        slot = block_data.get('slot', 0)
        block_height = block_data.get('block_height', 0)
        parent_slot = block_data.get('parent_slot', 0)

        if block_height > slot:
            issues.append(f"block_height ({block_height}) > slot ({slot})")

        if parent_slot >= slot:
            issues.append(f"parent_slot ({parent_slot}) >= slot ({slot})")

        # Calculate skipped slots (indicates network health)
        skipped_slots = slot - parent_slot - 1
        if skipped_slots > 10:
            warnings.append(f"Many skipped slots: {skipped_slots}")
        metrics['skipped_slots'] = skipped_slots

        # Timestamp validation
        timestamp = block_data.get('timestamp')
        if timestamp:
            now = datetime.now()
            if timestamp > now + timedelta(seconds=self.SOLANA_TIMESTAMP_TOLERANCE_SECONDS):
                issues.append(f"Timestamp in future: {timestamp}")

            age_seconds = (now - timestamp).total_seconds()
            metrics['timestamp_age_seconds'] = age_seconds

        # Transaction count
        tx_count = block_data.get('transaction_count', 0)
        if tx_count < 0:
            issues.append(f"Negative transaction count: {tx_count}")
        elif tx_count > self.SOLANA_TX_PER_BLOCK_MAX:
            warnings.append(f"Very high transaction count: {tx_count}")

        metrics['tx_count'] = tx_count

        quality_level = self._determine_quality_level(issues, warnings)
        metrics['quality_score'] = self._calculate_quality_score(issues, warnings)

        return ValidationResult(
            is_valid=len(issues) == 0,
            quality_level=quality_level,
            issues=issues,
            warnings=warnings,
            metrics=metrics
        )

    def validate_solana_transaction(self, tx_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate a Solana transaction for data quality.

        VERACITY CHECKS:
        1. Signature format (base58 encoded)
        2. Fee is reasonable (minimum 5000 lamports)
        3. Status is valid ('success' or 'failed')
        """
        issues = []
        warnings = []
        metrics = {}

        # Completeness
        required_fields = ['signature', 'slot', 'fee', 'status']
        missing = [f for f in required_fields if f not in tx_data or tx_data[f] is None]
        if missing:
            issues.append(f"Missing fields: {missing}")

        metrics['completeness'] = (len(required_fields) - len(missing)) / len(required_fields)

        # Fee validation
        fee = tx_data.get('fee', -1)
        if fee < 0:
            issues.append(f"Negative fee: {fee}")
        elif fee < self.SOLANA_FEE_MIN_LAMPORTS and fee > 0:
            warnings.append(f"Fee below expected minimum: {fee} lamports")

        # Status validation
        status = tx_data.get('status', '')
        if status not in ('success', 'failed'):
            issues.append(f"Invalid status: {status}")

        if status == 'failed':
            metrics['is_failed'] = 1.0
        else:
            metrics['is_failed'] = 0.0

        # Signature format (should be base58, typically 87-88 characters)
        signature = tx_data.get('signature', '')
        if len(signature) < 80 or len(signature) > 90:
            warnings.append(f"Unusual signature length: {len(signature)}")

        quality_level = self._determine_quality_level(issues, warnings)
        metrics['quality_score'] = self._calculate_quality_score(issues, warnings)

        return ValidationResult(
            is_valid=len(issues) == 0,
            quality_level=quality_level,
            issues=issues,
            warnings=warnings,
            metrics=metrics
        )

    def _is_valid_hash(self, hash_str: str, expected_length: int) -> bool:
        """Check if a string is a valid hexadecimal hash of expected length."""
        if not hash_str or len(hash_str) != expected_length:
            return False
        try:
            int(hash_str, 16)
            return True
        except ValueError:
            return False

    def _determine_quality_level(self, issues: List[str], warnings: List[str]) -> QualityLevel:
        """Determine overall quality level based on issues and warnings."""
        if len(issues) > 2:
            return QualityLevel.INVALID
        elif issues:
            return QualityLevel.LOW
        elif warnings:
            return QualityLevel.MEDIUM
        return QualityLevel.HIGH

    def _calculate_quality_score(self, issues: List[str], warnings: List[str]) -> float:
        """
        Calculate a numeric quality score from 0.0 to 1.0.

        Scoring:
        - Start at 1.0
        - Subtract 0.2 for each issue
        - Subtract 0.05 for each warning
        - Minimum score is 0.0
        """
        score = 1.0
        score -= len(issues) * 0.2
        score -= len(warnings) * 0.05
        return max(0.0, score)

    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all validations performed.

        Returns statistics useful for monitoring data quality over time.
        """
        total = self.validation_counts['total']
        if total == 0:
            return {"message": "No validations performed yet"}

        return {
            "total_validations": total,
            "passed": self.validation_counts['passed'],
            "failed": self.validation_counts['failed'],
            "with_warnings": self.validation_counts['warnings'],
            "pass_rate": round(self.validation_counts['passed'] / total * 100, 2),
            "fail_rate": round(self.validation_counts['failed'] / total * 100, 2)
        }


def log_quality_issue(source: str, record_type: str, record_id: str,
                      result: ValidationResult, client) -> None:
    """
    Log a data quality issue to the data_quality table for tracking.

    This creates an audit trail of data quality issues, enabling:
    - Trend analysis of data quality over time
    - Root cause analysis of data issues
    - Alerting on quality degradation

    Args:
        source: The blockchain source (bitcoin, solana, ethereum)
        record_type: Type of record (block, transaction)
        record_id: Unique identifier for the record
        result: ValidationResult from validation
        client: ClickHouse client for inserting quality records
    """
    if not result.issues and not result.warnings:
        return  # Only log if there are issues

    try:
        client.insert('data_quality', [{
            'detected_at': datetime.now(),
            'source': source,
            'record_type': record_type,
            'record_id': record_id,
            'quality_level': result.quality_level.value,
            'quality_score': result.metrics.get('quality_score', 0.0),
            'issue_count': len(result.issues),
            'warning_count': len(result.warnings),
            'issues': '; '.join(result.issues) if result.issues else '',
            'warnings': '; '.join(result.warnings) if result.warnings else ''
        }])
    except Exception as e:
        logger.error(f"Failed to log quality issue: {e}")
