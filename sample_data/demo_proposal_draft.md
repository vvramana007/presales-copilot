# Proposal Draft — Acme Insurance Group *(demo output — canned data)*

*Generated draft. Every claim cites an asset ID; [TO VERIFY] items need human input. Requires review and approval before any client use.*

## Executive Summary

Acme Insurance Group requires a partner who has already delivered cloud-native claims platforms at carrier scale — not one who will learn on your project. We bring directly applicable, recent experience: a winning claims automation platform with Guidewire ClaimCenter integration and AI document classification running at 97% production accuracy [AST-001], a claimant self-service portal with English/Spanish localization [AST-003], and an audit-traceable 40 TB data migration completed with zero reconciliation failures [AST-005]. Our proposed solution meets 13 of your 16 stated requirements with proven, referenceable capability, and we identify the remaining items transparently in Section 2 with a concrete plan for each.

## Understanding of Requirements

Your RFP describes three connected goals. First, modernize claims intake at scale (R-001, R-002): a cloud-native platform handling 50,000+ claims/day, integrated with your existing Guidewire ClaimCenter estate. Second, apply AI where it measurably reduces handling cost (R-003, R-007): document classification at 95%+ accuracy and real-time fraud scoring. Third, deliver safely (R-005, R-006, R-009, R-010): encrypted, SOC 2-compliant, US-hosted, with 24x7 support and a fully auditable 40 TB history migration. We also note the commercial terms in clauses 4.2 and 4.3 (liability and IP transfer), addressed in our commercial response with proposed alternative language [TO VERIFY: legal review of final positions].

## Proposed Solution

We propose a phased build on AWS following our claims-platform architecture proven at Midwest Mutual [AST-001]: event-driven intake services scaled for 50k+ claims/day, integration with ClaimCenter via published APIs, and our Document AI accelerator [AST-002] for correspondence classification — deployed at 96–98% accuracy in three prior carrier engagements, exceeding your 95% requirement. For real-time fraud scoring (R-007) we will implement our real-time scoring reference architecture (Kafka ingestion, feature store, model endpoints; p99 latency 400ms at 5,000 TPS) [AST-004]. The claimant portal follows our React Native mobile-first pattern with Spanish localization and WCAG 2.1 AA accessibility [AST-003]. Security and hosting requirements are met by our standard SOC 2 Type II / AES-256 / US-only hosting patterns [AST-007].

## Relevant Experience

Three engagements map directly to your scope. Midwest Mutual Insurance: cloud-native claims platform with Guidewire integration, delivered in 11 months, 38% claims-handling cost reduction in year one [AST-001]. Northern Casualty: 40 TB audit-traceable policy data migration in 8 months, zero reconciliation failures — the same scale as your requirement 3.10 [AST-005]. Atlantic Specialty: a governed, human-in-the-loop GenAI assistant, demonstrating the AI-governance discipline your regulators will expect [AST-009]. Insurance-industry references for all three are available on request (R-015).

## Delivery Approach and Team

We propose four phases over 12 months: foundation and integration (months 1–3), claims intake and document AI (months 4–7), fraud scoring and portal (months 8–10), migration completion and hardening (months 11–12) — meeting clause 4.1. Migration runs in parallel streams from month 2 using the factory approach from [AST-005]. Support transitions to our 24x7 model at go-live [AST-008]; we propose our premium tier to meet your 15-minute Severity-1 response requirement (R-009). Knowledge transfer follows our standard methodology [AST-008] with paired delivery and documented runbooks throughout, not as an end-phase afterthought.
