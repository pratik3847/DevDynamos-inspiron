import React, { useEffect, useState } from 'react';
import { ChevronDown, ChevronRight, Search, Filter, HelpCircle, ExternalLink, AlertCircle } from 'lucide-react';

interface ClaimsTableProps {
  file: {
    file_id: string;
    filename: string;
    parsed_data: any;
  };
}

interface Claim {
  claim_submitter_identifier: string;
  claim_status_code: string;
  status_description: string;
  total_claim_charge_amount: number;
  claim_payment_amount: number;
  patient_responsibility_amount: number;
  adjustments: Adjustment[];
  adjustment_summary: {
    total_adjustments: number;
    total_adjustment_amount: number;
    unique_reason_codes: string[];
  };
  patient?: {
    first_name: string;
    last_name: string;
  };
  dates?: { [key: string]: string };
}

interface Adjustment {
  reason_code: string;
  adjustment_amount: number;
  quantity: number;
  group_code: string;
}

const ClaimsTable: React.FC<ClaimsTableProps> = ({ file }) => {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedClaims, setExpandedClaims] = useState<Set<string>>(new Set());
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [carcExplanations, setCarcExplanations] = useState<{ [key: string]: any }>({});
  const [loadingExplanations, setLoadingExplanations] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchClaims();
  }, [file.file_id]);

  const fetchClaims = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/parser/claim-details/${file.file_id}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setClaims(data.claims || []);
      }
    } catch (error) {
      console.error('Error fetching claims:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCarcExplanation = async (reasonCode: string) => {
    if (carcExplanations[reasonCode] || loadingExplanations.has(reasonCode)) {
      return;
    }

    setLoadingExplanations(prev => new Set([...prev, reasonCode]));

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/parser/explain-adjustment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          reason_codes: [reasonCode],
          context: `Claim adjustment in remittance file ${file.filename}`
        })
      });

      if (response.ok) {
        const data = await response.json();
        setCarcExplanations(prev => ({
          ...prev,
          [reasonCode]: data.explanations[reasonCode]
        }));
      }
    } catch (error) {
      console.error('Error fetching CARC explanation:', error);
    } finally {
      setLoadingExplanations(prev => {
        const newSet = new Set(prev);
        newSet.delete(reasonCode);
        return newSet;
      });
    }
  };

  const toggleClaimExpansion = (claimId: string) => {
    setExpandedClaims(prev => {
      const newSet = new Set(prev);
      if (newSet.has(claimId)) {
        newSet.delete(claimId);
      } else {
        newSet.add(claimId);
      }
      return newSet;
    });
  };

  const getStatusColor = (statusCode: string): string => {
    const colorMap: { [key: string]: string } = {
      '1': 'text-green-700 bg-green-50',
      '2': 'text-blue-700 bg-blue-50',
      '3': 'text-purple-700 bg-purple-50',
      '4': 'text-red-700 bg-red-50'
    };
    return colorMap[statusCode] || 'text-gray-700 bg-gray-50';
  };

  const getGroupCodeName = (groupCode: string): string => {
    const groupMap: { [key: string]: string } = {
      'PR': 'Patient Responsibility',
      'CO': 'Contractual Obligation',
      'OA': 'Other Adjustment',
      'PI': 'Payer Initiated'
    };
    return groupMap[groupCode] || groupCode;
  };

  // Filter claims based on search and status
  const filteredClaims = claims.filter(claim => {
    const matchesSearch = !searchTerm || 
      claim.claim_submitter_identifier.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (claim.patient && 
        `${claim.patient.first_name} ${claim.patient.last_name}`.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesStatus = statusFilter === 'all' || claim.claim_status_code === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading claims...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Search and Filters */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search by claim ID or patient name..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none bg-white"
              >
                <option value="all">All Claims</option>
                <option value="1">Processed as Primary</option>
                <option value="2">Processed as Secondary</option>
                <option value="3">Processed as Tertiary</option>
                <option value="4">Denied</option>
              </select>
            </div>
          </div>
          <div className="text-sm text-gray-600">
            Showing {filteredClaims.length} of {claims.length} claims
          </div>
        </div>
      </div>

      {/* Claims Table */}
      <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-8"></th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Claim ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Patient</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Billed</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Paid</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Patient Resp.</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Adjustments</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredClaims.map((claim) => (
                <React.Fragment key={claim.claim_submitter_identifier}>
                  {/* Main Claim Row */}
                  <tr className="hover:bg-gray-50 cursor-pointer" onClick={() => toggleClaimExpansion(claim.claim_submitter_identifier)}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {expandedClaims.has(claim.claim_submitter_identifier) ? (
                        <ChevronDown className="w-4 h-4 text-gray-500" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-gray-500" />
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {claim.claim_submitter_identifier}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {claim.patient ? `${claim.patient.first_name} ${claim.patient.last_name}` : 'N/A'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(claim.claim_status_code)}`}>
                        {claim.status_description}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                      ${claim.total_claim_charge_amount.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                      ${claim.claim_payment_amount.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                      ${claim.patient_responsibility_amount.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      {claim.adjustment_summary.total_adjustments > 0 ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                          {claim.adjustment_summary.total_adjustments} adjustments
                        </span>
                      ) : (
                        <span className="text-gray-400 text-sm">None</span>
                      )}
                    </td>
                  </tr>

                  {/* Expanded Claim Details */}
                  {expandedClaims.has(claim.claim_submitter_identifier) && (
                    <tr>
                      <td colSpan={8} className="px-6 py-4 bg-gray-50">
                        <div className="space-y-4">
                          {/* Adjustments */}
                          {claim.adjustments.length > 0 && (
                            <div>
                              <h4 className="text-sm font-semibold text-gray-900 mb-3">Claim Adjustments</h4>
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {claim.adjustments.map((adjustment, index) => (
                                  <div key={index} className="bg-white rounded-lg border p-4">
                                    <div className="flex items-start justify-between">
                                      <div>
                                        <div className="flex items-center space-x-2">
                                          <span className="font-medium text-gray-900">
                                            CARC-{adjustment.reason_code}
                                          </span>
                                          <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded">
                                            {getGroupCodeName(adjustment.group_code)}
                                          </span>
                                        </div>
                                        <div className="text-sm text-gray-600 mt-1">
                                          Amount: ${adjustment.adjustment_amount.toLocaleString()}
                                          {adjustment.quantity > 0 && ` | Qty: ${adjustment.quantity}`}
                                        </div>
                                      </div>
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          fetchCarcExplanation(adjustment.reason_code);
                                        }}
                                        className="flex items-center px-3 py-1 text-xs text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-md transition-colors"
                                        disabled={loadingExplanations.has(adjustment.reason_code)}
                                      >
                                        {loadingExplanations.has(adjustment.reason_code) ? (
                                          <div className="animate-spin rounded-full h-3 w-3 border-b border-blue-600 mr-1"></div>
                                        ) : (
                                          <HelpCircle className="w-3 h-3 mr-1" />
                                        )}
                                        Explain
                                      </button>
                                    </div>

                                    {/* AI Explanation */}
                                    {carcExplanations[adjustment.reason_code] && (
                                      <div className="mt-3 p-3 bg-blue-50 rounded-lg border-l-4 border-blue-400">
                                        <div className="flex items-start">
                                          <AlertCircle className="w-4 h-4 text-blue-600 mt-0.5 mr-2 flex-shrink-0" />
                                          <div>
                                            <p className="text-sm text-blue-800 font-medium mb-1">AI Explanation:</p>
                                            <p className="text-sm text-blue-700">
                                              {carcExplanations[adjustment.reason_code].explanation}
                                            </p>
                                            <div className="flex items-center justify-between mt-2">
                                              <span className="text-xs text-blue-600">
                                                Confidence: {(carcExplanations[adjustment.reason_code].confidence * 100).toFixed(1)}%
                                              </span>
                                              <span className="text-xs text-blue-600">
                                                Source: {carcExplanations[adjustment.reason_code].source}
                                              </span>
                                            </div>
                                          </div>
                                        </div>
                                      </div>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Additional Claim Info */}
                          {claim.dates && Object.keys(claim.dates).length > 0 && (
                            <div>
                              <h4 className="text-sm font-semibold text-gray-900 mb-2">Service Dates</h4>
                              <div className="flex space-x-6">
                                {Object.entries(claim.dates).map(([qualifier, date]) => (
                                  <div key={qualifier}>
                                    <span className="text-xs text-gray-500">{getDateQualifierName(qualifier)}:</span>
                                    <span className="ml-2 text-sm text-gray-900">{formatDate(date)}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>

        {filteredClaims.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">No claims match your search criteria.</p>
          </div>
        )}
      </div>
    </div>
  );
};

// Helper functions
function getDateQualifierName(qualifier: string): string {
  const qualifierMap: { [key: string]: string } = {
    '232': 'Service Date',
    '050': 'Received Date',
    '036': 'Expiration Date'
  };
  return qualifierMap[qualifier] || qualifier;
}

function formatDate(dateString: string): string {
  if (!dateString) return 'N/A';
  
  // Handle CCYYMMDD format
  if (dateString.length === 8) {
    const year = dateString.substring(0, 4);
    const month = dateString.substring(4, 6);
    const day = dateString.substring(6, 8);
    return new Date(`${year}-${month}-${day}`).toLocaleDateString();
  }
  
  return new Date(dateString).toLocaleDateString();
}

export default ClaimsTable;