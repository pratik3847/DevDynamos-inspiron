import React, { useEffect, useState } from 'react';
import { DollarSign, FileText, Users, TrendingUp, CreditCard, Calendar, Building2 } from 'lucide-react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface PaymentOverviewProps {
  file: {
    file_id: string;
    filename: string;
    parsed_data: any;
  };
}

const PaymentOverview: React.FC<PaymentOverviewProps> = ({ file }) => {
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPaymentSummary();
  }, [file.file_id]);

  const fetchPaymentSummary = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/parser/payment-summary/${file.file_id}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSummary(data);
      }
    } catch (error) {
      console.error('Error fetching payment summary:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading payment overview...</span>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">Unable to load payment summary.</p>
      </div>
    );
  }

  // Prepare chart data
  const statusData = Object.entries(summary.summary?.claim_status_breakdown || {}).map(([status, count]) => ({
    name: getStatusName(status),
    value: count as number,
    color: getStatusColor(status)
  }));

  const adjustmentData = Object.entries(summary.summary?.top_adjustment_reasons || {})
    .slice(0, 8)
    .map(([code, count]) => ({
      code: `CARC-${code}`,
      count: count as number
    }));

  return (
    <div className="space-y-8">
      {/* Header Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Payment Amount"
          value={`$${summary.payment_info?.payment_amount?.toLocaleString() || '0.00'}`}
          icon={DollarSign}
          color="green"
        />
        <StatCard
          title="Total Claims"
          value={summary.summary?.total_claims?.toString() || '0'}
          icon={FileText}
          color="blue"
        />
        <StatCard
          title="Total Billed"
          value={`$${summary.summary?.total_billed_amount?.toLocaleString() || '0.00'}`}
          icon={TrendingUp}
          color="purple"
        />
        <StatCard
          title="Patient Responsibility"
          value={`$${summary.summary?.total_patient_responsibility?.toLocaleString() || '0.00'}`}
          icon={Users}
          color="orange"
        />
      </div>

      {/* Payment Information */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Payment Details</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="flex items-center">
            <CreditCard className="w-5 h-5 text-gray-400 mr-3" />
            <div>
              <p className="text-sm text-gray-600">Payment Method</p>
              <p className="font-medium text-gray-900">
                {getPaymentMethodName(summary.payment_info?.payment_method)}
              </p>
            </div>
          </div>
          <div className="flex items-center">
            <Calendar className="w-5 h-5 text-gray-400 mr-3" />
            <div>
              <p className="text-sm text-gray-600">Payment Date</p>
              <p className="font-medium text-gray-900">
                {formatDate(summary.payment_info?.payment_date) || 'Not specified'}
              </p>
            </div>
          </div>
          <div className="flex items-center">
            <Building2 className="w-5 h-5 text-gray-400 mr-3" />
            <div>
              <p className="text-sm text-gray-600">Payer</p>
              <p className="font-medium text-gray-900">
                {summary.payer_info?.name || 'Unknown Payer'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Claim Status Breakdown */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Claim Status Breakdown</h3>
          {statusData.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={statusData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {statusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No claim status data available</p>
          )}
        </div>

        {/* Top Adjustment Reasons */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Adjustment Reasons</h3>
          {adjustmentData.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={adjustmentData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="code" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#3B82F6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No adjustment data available</p>
          )}
        </div>
      </div>

      {/* Entity Information */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Payer Information */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Payer Information</h3>
          <div className="space-y-3">
            <div>
              <p className="text-sm text-gray-600">Name</p>
              <p className="font-medium text-gray-900">{summary.payer_info?.name || 'N/A'}</p>
            </div>
            {summary.payer_info?.address_line_1 && (
              <div>
                <p className="text-sm text-gray-600">Address</p>
                <div className="font-medium text-gray-900">
                  <p>{summary.payer_info.address_line_1}</p>
                  {summary.payer_info.address_line_2 && <p>{summary.payer_info.address_line_2}</p>}
                  <p>
                    {summary.payer_info.city}, {summary.payer_info.state} {summary.payer_info.zip_code}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Payee Information */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Payee Information</h3>
          <div className="space-y-3">
            <div>
              <p className="text-sm text-gray-600">Name</p>
              <p className="font-medium text-gray-900">{summary.payee_info?.name || 'N/A'}</p>
            </div>
            {summary.payee_info?.address_line_1 && (
              <div>
                <p className="text-sm text-gray-600">Address</p>
                <div className="font-medium text-gray-900">
                  <p>{summary.payee_info.address_line_1}</p>
                  {summary.payee_info.address_line_2 && <p>{summary.payee_info.address_line_2}</p>}
                  <p>
                    {summary.payee_info.city}, {summary.payee_info.state} {summary.payee_info.zip_code}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Helper Components and Functions
interface StatCardProps {
  title: string;
  value: string;
  icon: React.ElementType;
  color: 'green' | 'blue' | 'purple' | 'orange';
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon: Icon, color }) => {
  const colorClasses = {
    green: 'bg-green-50 text-green-600 border-green-200',
    blue: 'bg-blue-50 text-blue-600 border-blue-200',
    purple: 'bg-purple-50 text-purple-600 border-purple-200',
    orange: 'bg-orange-50 text-orange-600 border-orange-200'
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="flex items-center">
        <div className={`p-2 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
        <div className="ml-4">
          <p className="text-sm text-gray-600">{title}</p>
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  );
};

function getStatusName(code: string): string {
  const statusMap: { [key: string]: string } = {
    '1': 'Processed as Primary',
    '2': 'Processed as Secondary',
    '3': 'Processed as Tertiary',
    '4': 'Denied'
  };
  return statusMap[code] || `Status ${code}`;
}

function getStatusColor(code: string): string {
  const colorMap: { [key: string]: string } = {
    '1': '#10B981', // green
    '2': '#3B82F6', // blue
    '3': '#8B5CF6', // purple
    '4': '#EF4444'  // red
  };
  return colorMap[code] || '#6B7280';
}

function getPaymentMethodName(code: string): string {
  const methodMap: { [key: string]: string } = {
    'CHK': 'Check',
    'ACH': 'Electronic Transfer (ACH)',
    'C': 'Credit',
    'D': 'Debit'
  };
  return methodMap[code] || code || 'Unknown';
}

function formatDate(dateString: string): string | null {
  if (!dateString) return null;
  
  // Handle CCYYMMDD format
  if (dateString.length === 8) {
    const year = dateString.substring(0, 4);
    const month = dateString.substring(4, 6);
    const day = dateString.substring(6, 8);
    return new Date(`${year}-${month}-${day}`).toLocaleDateString();
  }
  
  return new Date(dateString).toLocaleDateString();
}

export default PaymentOverview;