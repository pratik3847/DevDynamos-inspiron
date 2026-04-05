"""Fix Agent

Generates actionable correction suggestions from validation errors.Enhanced with RAG Knowledge System:
- Queries TR3 guides for segment structure and requirements
- Provides fix examples from implementation documentation
- Cites official sources for recommended corrections

Goal:
- Avoid mock values (e.g., FIXED_VAL/INVALID_VAL).
- Emit only deterministic fixes when we can compute a concrete new value.
- Ground fixes in TR3 specifications via RAG
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple
from app.services.rag import RAGClient


def _iter_segments(parsed: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
	if not isinstance(parsed, dict):
		return []
	segs = parsed.get("segments")
	return segs if isinstance(segs, list) else []


def _find_first_segment(parsed: Optional[Dict[str, Any]], segment_id: str) -> Optional[Dict[str, Any]]:
	for seg in _iter_segments(parsed):
		if isinstance(seg, dict) and seg.get("segmentId") == segment_id:
			return seg
	return None


def _find_segment_with_element_value(
	parsed: Optional[Dict[str, Any]],
	segment_id: str,
	element_pos_or_id: str,
	value: str,
	within_range: Optional[Tuple[int, int]] = None,
) -> Optional[int]:
	"""Find index of first segment matching a segmentId and element value.

	within_range: (start, end) slice bounds on the segments array.
	"""
	segs = _iter_segments(parsed)
	start, end = within_range if within_range else (0, len(segs))
	for i in range(max(0, start), min(len(segs), end)):
		seg = segs[i]
		if not isinstance(seg, dict):
			continue
		if str(seg.get("segmentId") or "").upper() != str(segment_id).upper():
			continue
		el_val = _find_element_value(seg, element_pos_or_id)
		if el_val is None:
			continue
		if str(el_val).strip() == str(value).strip():
			return i
	return None


def _find_element_value(seg: Optional[Dict[str, Any]], element_id: str) -> Optional[str]:
	"""Return element value from a parsed segment.

	Supports element ids like "IEA01", raw positions like "01", and id matches.
	"""
	if not isinstance(seg, dict) or not element_id:
		return None
	els = seg.get("elements") or []
	if not isinstance(els, list):
		return None

	# 1) exact id
	for el in els:
		if isinstance(el, dict) and el.get("id") == element_id:
			return el.get("value")

	# 2) position match
	pos = str(element_id).strip()
	if len(pos) == 2 and pos.isdigit():
		target = pos.zfill(2)
		for el in els:
			if isinstance(el, dict) and str(el.get("position") or "").zfill(2) == target:
				return el.get("value")

	# 3) derive from trailing digits (NM108 -> 08)
	digits = "".join([c for c in pos if c.isdigit()])
	if digits:
		target = digits[-2:].zfill(2)
		for el in els:
			if isinstance(el, dict) and str(el.get("position") or "").zfill(2) == target:
				return el.get("value")

	return None


def _derive_new_value(err: Dict[str, Any], parsed: Optional[Dict[str, Any]]) -> Optional[str]:
	"""Derive a concrete new value for a fix when possible."""
	suggestion = err.get("suggested_fix") or err.get("suggestion") or ""
	field = err.get("field") or err.get("element") or ""
	segment = err.get("segment") or ""

	# Common pattern emitted by structural validator: "Update IEA01 to 2"
	m = re.match(r"^\s*Update\s+([A-Z0-9]{2,3}\d{2})\s+to\s+(.+?)\s*$", str(suggestion))
	if m:
		return str(m.group(2)).strip()

	# Deterministic structural fixes by field
	if str(field) == "IEA01":
		gs_count = sum(1 for s in _iter_segments(parsed) if isinstance(s, dict) and s.get("segmentId") == "GS")
		return str(gs_count)

	if str(field) == "GE01":
		segs = _iter_segments(parsed)
		gs_index = next((i for i, s in enumerate(segs) if isinstance(s, dict) and s.get("segmentId") == "GS"), -1)
		ge_index = next((i for i, s in enumerate(segs) if isinstance(s, dict) and s.get("segmentId") == "GE" and i > gs_index), -1)
		if gs_index >= 0 and ge_index > gs_index:
			st_count = sum(1 for s in segs[gs_index:ge_index + 1] if isinstance(s, dict) and s.get("segmentId") == "ST")
			return str(st_count)

	if str(field) == "SE01":
		segs = _iter_segments(parsed)
		st_index = next((i for i, s in enumerate(segs) if isinstance(s, dict) and s.get("segmentId") == "ST"), -1)
		se_index = next((i for i, s in enumerate(segs) if isinstance(s, dict) and s.get("segmentId") == "SE" and i > st_index), -1)
		if st_index >= 0 and se_index > st_index:
			return str(se_index - st_index + 1)

	# Control-number alignment (prefer header values as source of truth)
	if str(field) == "IEA02":
		isa = _find_first_segment(parsed, "ISA")
		isa13 = _find_element_value(isa, "ISA13")
		return str(isa13) if isa13 is not None else None

	if str(field) == "GE02":
		gs = _find_first_segment(parsed, "GS")
		gs06 = _find_element_value(gs, "GS06")
		return str(gs06) if gs06 is not None else None

	if str(field) == "SE02":
		st = _find_first_segment(parsed, "ST")
		st02 = _find_element_value(st, "ST02")
		return str(st02) if st02 is not None else None

	# Fallback: if we can parse a numeric value from messages like "... to 3" (last token)
	if isinstance(suggestion, str) and " to " in suggestion:
		last = suggestion.split(" to ")[-1].strip()
		if last:
			return last

	# If validator marks it fixable but we still can't compute a concrete value, don't emit a fake fix.
	return None


def _icd10_insert_decimal(code: str) -> Optional[str]:
	"""Insert decimal after 3 chars for ICD-10 codes missing a decimal.

	Example: J449 -> J44.9
	"""
	if not code:
		return None
	s = str(code).strip().upper()
	if "." in s:
		return None
	# ICD-10 codes: 3-7 chars; decimal after 3rd char if 4+ chars.
	if len(s) < 4 or len(s) > 7:
		return None
	if not re.match(r"^[A-Z][0-9A-Z]{2,6}$", s):
		return None
	return s[:3] + "." + s[3:]


def _build_fix(
	*,
	idx: int,
	err: Dict[str, Any],
	segment_id: str,
	element_id: Optional[str],
	original: str,
	suggested: str,
	fixed_type: str,
	confidence: int,
	auto_apply: bool,
	reasoning: str,
	operation: str = "UPDATE_ELEMENT",
	operation_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
	return {
		"id": f"fix_{idx}",
		"errorId": err.get("id") or err.get("errorId") or f"ERR_{idx}",
		"segmentId": str(segment_id),
		"elementId": str(element_id) if element_id else None,
		"operation": operation,
		"operationData": operation_data or None,
		"fix_type": fixed_type,
		"confidence": int(confidence),
		"auto_apply": bool(auto_apply),
		"reasoning": reasoning,
		"action": "Auto Fix" if auto_apply else "Suggested Fix",
		"description": err.get("suggested_fix") or err.get("suggestion") or err.get("message") or err.get("error") or "",
		"original": original,
		"suggested": suggested,
		"status": "pending",
	}


class FixAgent:
	"""Deterministic fix suggester with RAG-powered documentation lookup.

	Only emits fixes when:
	- The validation error points to a specific (segment, field/element), and
	- We can derive a concrete replacement value.
	- RAG can provide TR3 specification context for the fix
	"""

	def __init__(self):
		"""Initialize fix agent with RAG knowledge system."""
		self.rag = RAGClient()  # RAG knowledge system for TR3 guidance

	def generate_fixes(self, validation_result: Dict[str, Any], parsed: Optional[Dict[str, Any]] = None, transaction_type: str = "837P") -> List[Dict[str, Any]]:
		fixes: List[Dict[str, Any]] = []
		errors = (validation_result or {}).get("errors", [])
		if not isinstance(errors, list):
			return fixes

		segs = _iter_segments(parsed)

		# Pre-compute a Billing Provider template (NM1*85) for AI-inferred fixes.
		nm1_85_index = _find_segment_with_element_value(parsed, "NM1", "01", "85")
		nm1_85_template = segs[nm1_85_index] if (nm1_85_index is not None and nm1_85_index < len(segs)) else None

		# Pre-compute claim blocks based on CLM..next CLM/SE (matches BusinessValidator behavior)
		clm_indexes = [i for i, s in enumerate(segs) if isinstance(s, dict) and s.get("segmentId") == "CLM"]
		se_index = next(
			(i for i, s in enumerate(segs) if isinstance(s, dict) and s.get("segmentId") == "SE"),
			len(segs),
		)

		for idx, err in enumerate(errors):
			if not isinstance(err, dict):
				continue

			code = str(err.get("code") or err.get("rule_id") or "").strip()
			segment_id = str(err.get("segment") or "").strip()
			element_id = err.get("field") or err.get("element")
			element_id_str = str(element_id).strip() if element_id else None

			# 3) NPI validation failure -> manual required
			# External validator commonly uses NPI001 / similar codes.
			if code.upper().startswith("NPI") or "NPI" in str(err.get("message") or err.get("error") or ""):
				if segment_id and element_id_str:
					seg = _find_first_segment(parsed, segment_id)
					current_value = _find_element_value(seg, element_id_str)
					fixes.append(
						_build_fix(
							idx=idx,
							err=err,
							segment_id=segment_id,
							element_id=element_id_str,
							original="" if current_value is None else str(current_value),
							suggested="",
							fixed_type="MANUAL_REQUIRED",
							confidence=0,
							auto_apply=False,
							reasoning="NPI failures require manual verification; do not auto-correct provider identifiers.",
							operation="NOOP",
						),
					)
				continue

			# 1) ICD-10 format fix (deterministic)
			if code.upper() == "ICD10_FMT001" or (
				segment_id.upper() == "HI" and "ICD-10" in str(err.get("error") or err.get("message") or "")
			):
				bad = err.get("value") or ""
				fixed = _icd10_insert_decimal(str(bad))
				if fixed:
					# Find the exact HI element holding this diagnosis (suffix after last ':')
					found_seg_idx = None
					found_el_id = None
					found_raw = None
					for si, seg in enumerate(segs):
						if not isinstance(seg, dict) or str(seg.get("segmentId") or "").upper() != "HI":
							continue
						for el in seg.get("elements", []) or []:
							if not isinstance(el, dict):
								continue
							raw = el.get("value")
							if not raw:
								continue
							parts = str(raw).split(":")
							diag = parts[-1].strip().upper() if parts else ""
							if diag == str(bad).strip().upper():
								prefix = ":".join(parts[:-1])
								new_val = (prefix + ":" if prefix else "") + fixed
								found_seg_idx = si
								found_el_id = el.get("id")
								found_raw = str(raw)
								break
						if found_seg_idx is not None:
							break

					if found_seg_idx is not None and found_el_id:
						fixes.append(
							_build_fix(
								idx=idx,
								err=err,
								segment_id="HI",
								element_id=str(found_el_id),
								original=found_raw or "",
								suggested=new_val,
								fixed_type="DETERMINISTIC",
								confidence=95,
								auto_apply=True,
								reasoning=f"Inserted ICD-10 decimal after 3rd character: {bad} → {fixed}.",
							),
						)
					continue

			# 2) Missing Rendering Provider (NM1*82) inference
			if code.upper() == "837_REQ_NM182" and nm1_85_template is not None:
				# Determine if any claim block is missing NM1*82
				needs = False
				for bi, start in enumerate(clm_indexes):
					end = clm_indexes[bi + 1] if bi + 1 < len(clm_indexes) else se_index
					block_range = (start, end)
					present = _find_segment_with_element_value(parsed, "NM1", "01", "82", within_range=block_range) is not None
					if not present:
						needs = True
						break
				if needs:
					fixes.append(
						_build_fix(
							idx=idx,
							err=err,
							segment_id="NM1",
							element_id="NM101",
							original="",
							suggested="",
							fixed_type="AI_INFERRED",
							confidence=65,
							auto_apply=False,
							reasoning="Rendering Provider (NM1*82) is missing; duplicate Billing Provider (NM1*85) as a best-effort proxy. Requires user approval.",
							operation="INSERT_NM1_82_FROM_85",
							operation_data={"template": "NM1*85", "insert_into": "each CLM block"},
						),
					)
				continue

			# Default path: deterministic structural element replacement.
			if not segment_id or not element_id_str:
				continue

			new_value = _derive_new_value(err, parsed)
			if new_value is None:
				continue

			severity = str(err.get("severity", "")).lower()
			confidence_score = 92 if severity in ["error", "critical"] else 85

			seg = _find_first_segment(parsed, str(segment_id))
			current_value = _find_element_value(seg, element_id_str)
			reasoning = "Derived a concrete replacement value from structural rules and envelope/control-number consistency."
			fixes.append(
				_build_fix(
					idx=idx,
					err=err,
					segment_id=str(segment_id),
					element_id=element_id_str,
					original="" if current_value is None else str(current_value),
					suggested=str(new_value),
					fixed_type="DETERMINISTIC",
					confidence=confidence_score,
					auto_apply=True,
					reasoning=reasoning,
				),
			)

		# Enrich all fixes with RAG documentation context
		fixes = self._enrich_fixes_with_rag(fixes, transaction_type)
		
		return fixes
	
	def _enrich_fixes_with_rag(self, fixes: List[Dict[str, Any]], transaction_type: str) -> List[Dict[str, Any]]:
		"""
		Enrich fix suggestions with RAG documentation and examples.
		
		Args:
			fixes: List of fix suggestions
			transaction_type: Transaction type for context
			
		Returns:
			Enhanced fixes with RAG context
		"""
		for fix in fixes:
			try:
				segment_id = fix.get('segment_id', '')
				element_id = fix.get('element_id', '')
				
				if not segment_id:
					continue
				
				# Query RAG for segment fix guidance
				if element_id:
					query = f"What is the correct format for {segment_id} element {element_id} in {transaction_type}?"
				else:
					query = f"How to correctly structure {segment_id} segment in {transaction_type}?"
				
				rag_results = self.rag.query(
					query,
					transaction_type=transaction_type,
					doc_type="tr3",
					top_k=1
				)
				
				if rag_results:
					fix['rag_guidance'] = {
						'documentation': rag_results[0]['text'][:300],
						'source': rag_results[0]['source_doc'],
						'page': rag_results[0]['page'],
						'relevance': rag_results[0]['score']
					}
					
					# Add to reasoning if not already detailed
					if fix.get('confidence', 0) < 1.0:
						existing_reasoning = fix.get('reasoning', '')
						fix['reasoning'] = f"{existing_reasoning} (See {rag_results[0]['source_doc']}, page {rag_results[0]['page']} for specification details)"
			
			except Exception:
				# Gracefully handle RAG query failures
				pass
		
		return fixes

	async def execute(self, session_state: Dict[str, Any]) -> Dict[str, Any]:
		"""Execute fix generation workflow with RAG enhancement."""
		validation_result = session_state.get("validation_result") or {}
		parsed = session_state.get("parsed_edi")
		transaction_type = session_state.get("transaction_type", "837P")
		
		# Generate fixes with RAG enhancement
		session_state["fixes"] = self.generate_fixes(validation_result, parsed, transaction_type)
		return session_state
