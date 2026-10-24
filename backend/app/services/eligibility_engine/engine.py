from typing import List, Dict, Any
from app.models.schemas import UserProfile, Recommendation, EligibilityResponse
from app.services.rules_engine.parser import RulesParser

class EligibilityEngine:
    def __init__(self):
        self.parser = RulesParser()

    def _calculate_tax(self, income: float, regime: str, age: int) -> float:
        if income <= 0:
            return 0.0
            
        tax = 0.0
        if regime == "old":
            # Determine basic exemption limit
            if age >= 80:
                exemption = 500000
            elif age >= 60:
                exemption = 300000
            else:
                exemption = 250000
                
            if income <= exemption:
                return 0.0
                
            # Slabs
            if income > 1000000:
                tax += (income - 1000000) * 0.30
                tax += 500000 * 0.20
                tax += (1000000 - 500000 - exemption) * 0.05
            elif income > 500000:
                tax += (income - 500000) * 0.20
                tax += (500000 - exemption) * 0.05
            else:
                tax += (income - exemption) * 0.05
                
            # Rebate u/s 87A for old regime (income up to 5L)
            if income <= 500000:
                tax = max(0.0, tax - 12500)
                
        elif regime == "new":
            # Standard new regime slabs (FY 2023-24 onwards)
            if income <= 300000:
                return 0.0
            elif income <= 600000:
                tax += (income - 300000) * 0.05
            elif income <= 900000:
                tax += 300000 * 0.05 + (income - 600000) * 0.10
            elif income <= 1200000:
                tax += 300000 * 0.05 + 300000 * 0.10 + (income - 900000) * 0.15
            elif income <= 1500000:
                tax += 300000 * 0.05 + 300000 * 0.10 + 300000 * 0.15 + (income - 1200000) * 0.20
            else:
                tax += 300000 * 0.05 + 300000 * 0.10 + 300000 * 0.15 + 300000 * 0.20 + (income - 1500000) * 0.30
                
            # Rebate u/s 87A for new regime (income up to 7L)
            if income <= 700000:
                tax = max(0.0, tax - 25000)

        # Add 4% Health & Education Cess
        return tax * 1.04

    def _get_total_current_deductions(self, profile: UserProfile) -> float:
        if profile.tax_regime != "old":
            # Standard deduction
            return 50000.0 if profile.basic_salary > 0 else 0.0
            
        deductions = 0.0
        if profile.basic_salary > 0:
            deductions += 50000.0
            
        deductions += min(150000, profile.sec_80c_investments + profile.scss_investment + profile.ssy_investment)
        
        self_limit = 50000 if profile.age >= 60 else 25000
        parents_limit = 50000 if profile.parents_age >= 60 else 25000
        deductions += min(self_limit, profile.health_insurance_premium)
        deductions += min(parents_limit, profile.parents_health_insurance_premium)
        
        deductions += min(50000, profile.nps_contribution)
        deductions += min(200000, profile.home_loan_interest)
        deductions += self._calculate_hra(profile)
        
        return deductions

    def evaluate(self, profile: UserProfile) -> EligibilityResponse:
        schemes = self.parser.get_all_schemes()
        recommendations = []
        total_unclaimed_deductions = 0.0
        total_potential_benefit = 0.0
        high_priority_count = 0
        
        self.base_taxable_income = max(0, profile.annual_income - self._get_total_current_deductions(profile))
        
        # We need to track group_80c so we only recommend it once
        processed_80c_group = False

        for rule in schemes:
            if not self._check_eligibility(rule, profile):
                continue
                
            rec = self._process_rule(rule, profile, processed_80c_group)
            if rec and rec.gap_amount > 0:
                # If this was an 80C rule, mark group as processed so we don't duplicate
                limit_type = rule["deduction_limit"]["type"]
                if limit_type == "group_80c":
                    if processed_80c_group:
                        # Append the alternative to the existing 80c recommendation
                        for existing_rec in recommendations:
                            if existing_rec.scheme_id == "sec_80c" or existing_rec.category == "Investments":
                                existing_rec.recommendation += f" Alternatively, {rec.scheme_name}: {rec.recommendation}"
                                existing_rec.explanation += f" Or: {rec.explanation}"
                                existing_rec.references.extend(rec.references)
                                existing_rec.references = list(set(existing_rec.references))
                                break
                        continue
                    processed_80c_group = True
                
                recommendations.append(rec)
                
                if not rec.is_planning:
                    total_unclaimed_deductions += rec.gap_amount
                    total_potential_benefit += rec.potential_tax_benefit
                    if rec.priority_score >= 80:
                        high_priority_count += 1
                
        # Sort by priority
        recommendations.sort(key=lambda x: x.priority_score, reverse=True)

        return EligibilityResponse(
            status="success",
            recommendations=recommendations,
            total_unclaimed_deductions=total_unclaimed_deductions,
            total_potential_benefit=total_potential_benefit,
            high_priority_recommendation_count=high_priority_count
        )

    def _check_eligibility(self, rule: Dict[str, Any], profile: UserProfile) -> bool:
        conditions = rule.get("eligibility_conditions", {})
        
        if profile.tax_regime not in conditions.get("applicable_regimes", []):
            return False
            
        if "min_age" in conditions and profile.age < conditions["min_age"]:
            return False
            
        if "max_age" in conditions and profile.age > conditions["max_age"]:
            return False
            
        if conditions.get("requires_girl_child") and not profile.has_girl_child:
            return False
            
        return True

    def _process_rule(self, rule: Dict[str, Any], profile: UserProfile, processed_80c_group: bool) -> Recommendation:
        scheme_id = rule["scheme_id"]
        limit_data = rule["deduction_limit"]
        limit_type = limit_data["type"]
        
        max_amount = 0.0
        current_investment = 0.0
        is_planning = False
        
        if limit_type == "fixed":
            max_amount = limit_data["max_amount"]
            if scheme_id == "nps_80ccd_1b":
                current_investment = profile.nps_contribution
            elif scheme_id == "home_loan_interest_24b":
                current_investment = profile.home_loan_interest
                if current_investment == 0:
                    is_planning = True
        elif limit_type == "group_80c":
            max_amount = 150000
            current_investment = profile.sec_80c_investments + profile.scss_investment + profile.ssy_investment
        elif limit_type == "health_80d":
            self_limit = 50000 if profile.age >= 60 else 25000
            parents_limit = 50000 if profile.parents_age >= 60 else 25000
            max_amount = self_limit + parents_limit
            current_investment = min(self_limit, profile.health_insurance_premium) + min(parents_limit, profile.parents_health_insurance_premium)
        elif limit_type == "hra_calculation":
            max_amount = self._calculate_hra(profile)
            # User is already claiming it implicitly via rent_paid if they entered it
            current_investment = max_amount 
            if max_amount > 0:
                # We yield it as an optimized planning node to not inflate unclaimed gap
                is_planning = True
                gap = max_amount # Hack to show the amount
            else:
                return None

        # Cap current investment at max amount
        if current_investment > max_amount:
            current_investment = max_amount
            
        if limit_type != "hra_calculation":
            gap = max_amount - current_investment
            
        if gap <= 0 and not (limit_type == "hra_calculation" and max_amount > 0):
            return None
            
        # Realistic tax calculation
        current_tax = self._calculate_tax(self.base_taxable_income, profile.tax_regime, profile.age)
        new_tax = self._calculate_tax(max(0, self.base_taxable_income - gap), profile.tax_regime, profile.age)
        potential_benefit = max(0.0, current_tax - new_tax)
        
        # Special logic for Home Loan explanation if planning
        rec_text = rule["recommendation_text"]
        explanation = rule["explanation_template"].format(
            current_investment=current_investment,
            gap_amount=gap,
            max_amount=max_amount,
            tax_saved=potential_benefit,
            rent_paid=profile.rent_paid,
            basic_salary=profile.basic_salary
        )
        
        if is_planning and scheme_id == "home_loan_interest_24b":
            rec_text = "Planning to buy a house? You can claim up to ₹2,00,000 on home loan interest."
            explanation = f"If you take a home loan, you can claim the interest paid up to ₹{max_amount} under Section 24(b). This could save you up to ₹{potential_benefit} in taxes."

        if is_planning and scheme_id == "hra_sec_10_13a":
            rec_text = "HRA Exemption Optimized."
            explanation = f"Based on your rent of ₹{profile.rent_paid} and basic salary of ₹{profile.basic_salary}, you are eligible for an HRA exemption of ₹{max_amount}."

        return Recommendation(
            scheme_id=scheme_id,
            scheme_name=rule["scheme_name"],
            category=rule.get("category", "General"),
            priority_score=rule.get("priority_score", 0),
            triggered_rule="Investment below max limit" if limit_type != "hra_calculation" else "HRA exemption calculated",
            threshold_used=max_amount,
            current_investment=current_investment,
            gap_amount=gap,
            potential_tax_benefit=potential_benefit,
            recommendation=rec_text,
            explanation=explanation,
            references=rule.get("references", []),
            is_planning=is_planning
        )

    def _calculate_hra(self, profile: UserProfile) -> float:
        if profile.hra_received <= 0 or profile.rent_paid <= 0 or profile.basic_salary <= 0:
            return 0.0
        rent_minus_10_pct = profile.rent_paid - (0.10 * profile.basic_salary)
        pct_basic = 0.50 if profile.is_metro_city else 0.40
        salary_limit = pct_basic * profile.basic_salary
        
        return max(0.0, min(profile.hra_received, rent_minus_10_pct, salary_limit))
