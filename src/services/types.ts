export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  role: 'admin' | 'user';
  token?: string;
}

export type RuleCategory = 'Structural' | 'Business' | 'External';
export type RuleSeverity = 'Critical' | 'Error' | 'Warning' | 'Info';

export interface RuleDefinition {
  id: string;
  name: string;
  category: RuleCategory;
  severity: RuleSeverity;
  description: string;
  scope: string[];
  source: string;
  tags: string[];
  enabled: boolean;
  defaultEnabled: boolean;
  runtime: 'Realtime' | 'Batch' | 'External';
  lastUpdated: string;
  matchCodes?: string[];
}

export interface ValidationError {
  id: string;
  loop: string;
  segment: string;
  element: string;
  description: string;
  rule: string;
  severity: 'Critical' | 'Warning' | 'Info' | 'Error';
  lineNumber: number;
}

export interface FixSuggestion {
  id: string;
  errorId: string;
  original: string;
  suggested: string;
  confidence: 'High' | 'Medium' | 'Low';
  confidenceScore?: number;
  description: string;
  status: 'pending' | 'accepted' | 'rejected';
  segmentId?: string;
  elementId?: string;
  action?: string;

  fix_type?: 'DETERMINISTIC' | 'AI_INFERRED' | 'MANUAL_REQUIRED';
  auto_apply?: boolean;
  reasoning?: string;
  operation?: string;
  operationData?: any;
}

export interface AgentStatus {
  name: string;
  status: 'idle' | 'processing' | 'complete' | 'error';
  message: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface Session {
  id: string;
  filename: string;
  uploadDate: string;
  createdAt?: string;
  updatedAt?: string;
  status: 'Processing' | 'Requires Attention' | 'Clean' | 'Ready to Send';
  rawEdi: string;
  parsedJson: any;
  errors: ValidationError[];
  originalErrors?: ValidationError[];
  fixes: FixSuggestion[];
  chatHistory: ChatMessage[];
  agents: AgentStatus[];
  memberEnrollmentSummary?: MemberEnrollmentSummary;
}

export interface MemberEnrollmentSummaryMember {
  key: string;
  name: string;
  memberId: string;
  maintenanceCode: string;
  maintenanceLabel?: string;
  relationshipCode: string;
  hasCob: boolean;
  dependents: MemberEnrollmentSummaryMember[];
  familyGroup: string;
}

export interface MemberEnrollmentSummary {
  type: string;
  generatedAt?: string;
  families: MemberEnrollmentSummaryMember[];
  stats?: {
    totalMembers: number;
    totalSubscribers: number;
    totalDependents: number;
    totalCob: number;
    familyCount: number;
  };
}
