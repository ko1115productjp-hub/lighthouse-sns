/**
 * Output Detail Page - Display single output with citations and history
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation, Link } from 'react-router-dom';
import {
  outputsAPI,
  citationsAPI,
  agreementsAPI,
  outputFollowAPI,
  Output,
  OutputFollowStats,
  HashVerificationResponse,
  CitationWithOutput,
  CitationStats,
} from '../lib/api';
import { useAuthStore } from '../store/authStore';
import { OutputFollowButton } from '../components/OutputFollowButton';

export function OutputDetail() {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuthStore();

  const [output, setOutput] = useState<Output | null>(null);
  const [history, setHistory] = useState<Output[]>([]);
  const [citingOutputs, setCitingOutputs] = useState<CitationWithOutput[]>([]);
  const [citedOutputs, setCitedOutputs] = useState<CitationWithOutput[]>([]);
  const [citationStats, setCitationStats] = useState<CitationStats | null>(null);
  const [agreements, setAgreements] = useState<any[]>([]);
  const [hasAgreed, setHasAgreed] = useState(false);
  const [outputFollowStats, setOutputFollowStats] = useState<OutputFollowStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'content' | 'history' | 'citations'>('content');
  const [citationSubTab, setCitationSubTab] = useState<'citing' | 'cited'>('citing');
  const [verificationResult, setVerificationResult] = useState<HashVerificationResponse | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [showVerificationModal, setShowVerificationModal] = useState(false);

  useEffect(() => {
    if (id) {
      loadOutput();
      loadHistory();
      loadCitations();
      loadAgreements();
      loadOutputFollowStats();
    }
  }, [id]);

  const loadOutput = async () => {
    if (!id) return;

    try {
      const response = await outputsAPI.get(id);
      setOutput(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load output');
    } finally {
      setIsLoading(false);
    }
  };

  const loadHistory = async () => {
    if (!id) return;

    try {
      const response = await outputsAPI.getHistory(id);
      setHistory(response.data);
    } catch (err) {
      console.error('Failed to load history:', err);
    }
  };

  const loadCitations = async () => {
    if (!id) return;

    try {
      // Load citing outputs (incoming citations - outputs that cite this one)
      const citingResponse = await citationsAPI.getCiting(id);
      setCitingOutputs(citingResponse.data);

      // Load cited outputs (outgoing citations - outputs this one cites)
      const citedResponse = await citationsAPI.getCited(id);
      setCitedOutputs(citedResponse.data);

      // Load citation statistics
      const statsResponse = await citationsAPI.getStats(id);
      setCitationStats(statsResponse.data);
    } catch (err) {
      console.error('Failed to load citations:', err);
    }
  };

  const loadAgreements = async () => {
    if (!id) return;

    try {
      const response = await agreementsAPI.getUsersWhoAgreed(id);
      setAgreements(response.data);

      // Check if current user has agreed
      if (user) {
        const userAgreement = response.data.find((a: any) => a.user_id === user.id);
        setHasAgreed(!!userAgreement);
      }
    } catch (err) {
      console.error('Failed to load agreements:', err);
    }
  };

  const loadOutputFollowStats = async () => {
    if (!id) return;

    try {
      const response = await outputFollowAPI.getOutputStats(id);
      setOutputFollowStats(response.data);
    } catch (err) {
      console.error('Failed to load output follow stats:', err);
    }
  };

  const handleAgree = async () => {
    if (!id) return;

    try {
      if (hasAgreed) {
        // Remove agreement
        await agreementsAPI.removeAgreement(id);
        setHasAgreed(false);
        setAgreements(agreements.filter((a) => a.user_id !== user?.id));
      } else {
        // Add agreement
        const response = await agreementsAPI.agree(id);
        setHasAgreed(true);
        setAgreements([...agreements, response.data]);
      }
    } catch (err: any) {
      console.error('Failed to toggle agreement:', err);
    }
  };

  const handleVerifyHash = async () => {
    if (!id) return;

    setIsVerifying(true);
    setVerificationResult(null);

    try {
      const response = await outputsAPI.verifyHash(id);
      setVerificationResult(response.data);
      setShowVerificationModal(true);
    } catch (err: any) {
      console.error('Failed to verify hash:', err);
      setVerificationResult({
        output_id: id,
        content_hash_valid: false,
        full_hash_valid: false,
        hash_chain_valid: false,
        message: err.response?.data?.detail || 'Failed to verify hash',
      });
      setShowVerificationModal(true);
    } finally {
      setIsVerifying(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      science: 'bg-blue-100 text-blue-800',
      art: 'bg-purple-100 text-purple-800',
      philosophy: 'bg-green-100 text-green-800',
      technology: 'bg-yellow-100 text-yellow-800',
      society: 'bg-red-100 text-red-800',
      script: 'bg-pink-100 text-pink-800',
      place: 'bg-teal-100 text-teal-800',
      experience: 'bg-orange-100 text-orange-800',
      other: 'bg-gray-100 text-gray-800',
    };
    return colors[category] || colors.other;
  };

  const getCitationTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      agree: '✅ Agree',
      criticize: '🔍 Criticize',
      develop: '🚀 Develop',
      reference: '📚 Reference',
    };
    return labels[type] || type;
  };

  const getCitationTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      agree: 'bg-green-100 text-green-800',
      criticize: 'bg-red-100 text-red-800',
      develop: 'bg-purple-100 text-purple-800',
      reference: 'bg-blue-100 text-blue-800',
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <p className="mt-4 text-gray-600">Loading output...</p>
      </div>
    );
  }

  if (error || !output) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-red-900 mb-2">Error</h2>
          <p className="text-red-800">{error || 'Output not found'}</p>
          <button
            onClick={() => navigate('/timeline')}
            className="mt-4 text-blue-600 hover:text-blue-700 font-medium"
          >
            ← Back to Timeline
          </button>
        </div>
      </div>
    );
  }

  const isAuthor = user?.id === output.user_id;

  return (
    <div className="max-w-4xl mx-auto">
      {/* Success Message */}
      {location.state?.noveltyScore !== undefined && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <h3 className="text-green-900 font-semibold mb-1">✅ Output Created Successfully!</h3>
          <p className="text-green-800 text-sm">
            Novelty Score: <strong>{(location.state.noveltyScore * 100).toFixed(1)}%</strong>
            {location.state.noveltyScore >= 0.5 ? ' - Published as Public' : ' - Published as Private'}
          </p>
        </div>
      )}

      {location.state?.updated && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <h3 className="text-green-900 font-semibold">✅ Output Updated Successfully!</h3>
        </div>
      )}

      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-gray-300 rounded-full"></div>
            <div>
              <p className="text-sm font-medium text-gray-900">
                User #{output.user_id.slice(0, 8)}
              </p>
              <p className="text-xs text-gray-500">{formatDate(output.created_at)}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${getCategoryColor(output.category)}`}>
              {output.category}
            </span>
            {output.visibility === 'private' && (
              <span className="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
                🔒 Private
              </span>
            )}
            {output.novelty_score !== undefined && output.novelty_score >= 0.5 && (
              <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                ✨ High Novelty
              </span>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="prose max-w-none mb-4">
          <p className="text-gray-800 whitespace-pre-wrap">{output.content}</p>
        </div>

        {/* Tags */}
        {output.tags && output.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            {output.tags.map((tag) => (
              <span key={tag} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-md">
                #{tag}
              </span>
            ))}
          </div>
        )}

        {/* Metadata */}
        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-100 text-sm text-gray-600">
          <div>
            <span className="font-medium">Output ID:</span>{' '}
            <span className="font-mono text-xs">{output.id}</span>
          </div>
          <div>
            <span className="font-medium">Version:</span> {output.version}
          </div>
          {output.novelty_score !== undefined && (
            <div>
              <span className="font-medium">Novelty Score:</span>{' '}
              {(output.novelty_score * 100).toFixed(1)}%
            </div>
          )}
          <div>
            <span className="font-medium">Agreements:</span> {agreements.length}
          </div>
          {outputFollowStats && (
            <div>
              <span className="font-medium">Followers:</span> {outputFollowStats.follower_count}
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-100 mt-4">
          <div className="flex items-center space-x-3">
            <button
              onClick={handleAgree}
              className={`px-4 py-2 rounded-md text-sm font-medium transition ${
                hasAgreed
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {hasAgreed ? '✓ Agreed' : 'Agree'} ({agreements.length})
            </button>
            <Link
              to={`/create?cite=${output.id}`}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-200 transition"
            >
              📝 Cite This
            </Link>
            {outputFollowStats && (
              <OutputFollowButton
                outputId={output.id}
                initialIsFollowing={outputFollowStats.is_following}
                onFollowChange={(following) => {
                  setOutputFollowStats({
                    ...outputFollowStats,
                    is_following: following,
                    follower_count: following
                      ? outputFollowStats.follower_count + 1
                      : outputFollowStats.follower_count - 1,
                  });
                }}
              />
            )}
          </div>
          {isAuthor && (
            <Link
              to={`/output/${output.id}/edit`}
              className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 transition"
            >
              Edit
            </Link>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="mb-4 border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('content')}
            className={`${
              activeTab === 'content'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            Details
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`${
              activeTab === 'history'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            Version History ({history.length})
          </button>
          <button
            onClick={() => setActiveTab('citations')}
            className={`${
              activeTab === 'citations'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            Citations ({citationStats?.incoming_citations || 0} / {citationStats?.outgoing_citations || 0})
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'content' && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Technical Details</h3>
          <dl className="space-y-3 text-sm">
            <div>
              <dt className="font-medium text-gray-700">Content Hash (SHA-256)</dt>
              <dd className="mt-1 font-mono text-xs text-gray-600 break-all">
                {output.content_hash}
              </dd>
            </div>
            {output.previous_hash && (
              <div>
                <dt className="font-medium text-gray-700">Previous Hash</dt>
                <dd className="mt-1 font-mono text-xs text-gray-600 break-all">
                  {output.previous_hash}
                </dd>
              </div>
            )}
            <div>
              <dt className="font-medium text-gray-700">Created At</dt>
              <dd className="mt-1 text-gray-600">{formatDate(output.created_at)}</dd>
            </div>
            <div>
              <dt className="font-medium text-gray-700">Last Updated</dt>
              <dd className="mt-1 text-gray-600">{formatDate(output.updated_at || output.created_at)}</dd>
            </div>
          </dl>

          {/* Hash Verification Button - Only for public outputs */}
          {output.visibility === 'public' && (
            <div className="mt-6 pt-4 border-t border-gray-200">
              <button
                onClick={handleVerifyHash}
                disabled={isVerifying}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition text-sm font-medium flex items-center justify-center"
              >
                {isVerifying ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Verifying...
                  </>
                ) : (
                  <>
                    🔐 Verify Hash Integrity
                  </>
                )}
              </button>
              <p className="mt-2 text-xs text-gray-500 text-center">
                This feature is only available for public outputs to ensure transparency and immutability.
              </p>
            </div>
          )}

          {/* Note for private outputs */}
          {output.visibility === 'private' && (
            <div className="mt-6 pt-4 border-t border-gray-200">
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-600 text-center">
                  Hash verification is not available for private outputs.
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'history' && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Version History</h3>
          {history.length === 0 ? (
            <p className="text-gray-600 text-sm">No version history available</p>
          ) : (
            <div className="space-y-4">
              {history.map((version, index) => (
                <div key={version.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-semibold text-gray-900">
                      Version {version.version}
                      {index === 0 && (
                        <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded">
                          Current
                        </span>
                      )}
                    </span>
                    <span className="text-xs text-gray-500">{formatDate(version.updated_at || version.created_at)}</span>
                  </div>
                  <p className="text-sm text-gray-700 mb-2 line-clamp-3">{version.content}</p>
                  <p className="text-xs text-gray-500 font-mono">Hash: {version.content_hash}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'citations' && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Citations</h3>
            {citationStats && (
              <div className="flex items-center space-x-4 text-sm text-gray-600">
                <span>
                  <span className="font-medium">Cited by:</span> {citationStats.incoming_citations}
                </span>
                <span>
                  <span className="font-medium">Cites:</span> {citationStats.outgoing_citations}
                </span>
              </div>
            )}
          </div>

          {/* Citation Stats by Type */}
          {citationStats && citationStats.incoming_citations > 0 && (
            <div className="mb-4 p-3 bg-gray-50 rounded-lg">
              <p className="text-xs font-medium text-gray-700 mb-2">Incoming Citations by Type:</p>
              <div className="flex flex-wrap gap-2">
                {Object.entries(citationStats.incoming_by_type).map(([type, count]) => (
                  count > 0 && (
                    <span key={type} className={`px-2 py-1 rounded-md text-xs font-medium ${getCitationTypeColor(type)}`}>
                      {getCitationTypeLabel(type)}: {count}
                    </span>
                  )
                ))}
              </div>
            </div>
          )}

          {/* Sub-tabs for citing vs cited */}
          <div className="mb-4 border-b border-gray-200">
            <nav className="-mb-px flex space-x-6">
              <button
                onClick={() => setCitationSubTab('citing')}
                className={`${
                  citationSubTab === 'citing'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap pb-3 px-1 border-b-2 font-medium text-sm`}
              >
                Cited By ({citingOutputs.length})
              </button>
              <button
                onClick={() => setCitationSubTab('cited')}
                className={`${
                  citationSubTab === 'cited'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap pb-3 px-1 border-b-2 font-medium text-sm`}
              >
                Cites ({citedOutputs.length})
              </button>
            </nav>
          </div>

          {/* Citing Outputs (Incoming Citations) */}
          {citationSubTab === 'citing' && (
            <div className="space-y-3">
              {citingOutputs.length === 0 ? (
                <p className="text-gray-600 text-sm">No outputs cite this work yet</p>
              ) : (
                citingOutputs.map((citation) => (
                  <div key={citation.id} className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 rounded-md text-xs font-medium ${getCitationTypeColor(citation.citation_type)}`}>
                          {getCitationTypeLabel(citation.citation_type)}
                        </span>
                        <span className={`px-2 py-1 rounded-md text-xs font-medium ${getCategoryColor(citation.source_output.category)}`}>
                          {citation.source_output.category}
                        </span>
                      </div>
                      <span className="text-xs text-gray-500">
                        {formatDate(citation.created_at)}
                      </span>
                    </div>

                    {citation.excerpt && (
                      <div className="mb-2 p-2 bg-gray-50 rounded border-l-2 border-blue-300">
                        <p className="text-sm text-gray-700 italic">"{citation.excerpt}"</p>
                      </div>
                    )}

                    <Link
                      to={`/output/${citation.source_output.id}`}
                      className="block p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition"
                    >
                      <div className="flex items-center space-x-2 mb-2">
                        <div className="w-6 h-6 bg-gray-300 rounded-full"></div>
                        <span className="text-sm font-medium text-gray-900">
                          {citation.source_output.author.display_name}
                        </span>
                        <span className="text-xs text-gray-500">
                          @{citation.source_output.author.username}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 line-clamp-2">
                        {citation.source_output.content}
                      </p>
                      <p className="text-xs text-blue-600 mt-2">View full output →</p>
                    </Link>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Cited Outputs (Outgoing Citations) */}
          {citationSubTab === 'cited' && (
            <div className="space-y-3">
              {citedOutputs.length === 0 ? (
                <p className="text-gray-600 text-sm">This output doesn't cite any other works</p>
              ) : (
                citedOutputs.map((citation) => (
                  <div key={citation.id} className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 rounded-md text-xs font-medium ${getCitationTypeColor(citation.citation_type)}`}>
                          {getCitationTypeLabel(citation.citation_type)}
                        </span>
                        <span className={`px-2 py-1 rounded-md text-xs font-medium ${getCategoryColor(citation.source_output.category)}`}>
                          {citation.source_output.category}
                        </span>
                      </div>
                      <span className="text-xs text-gray-500">
                        {formatDate(citation.created_at)}
                      </span>
                    </div>

                    {citation.excerpt && (
                      <div className="mb-2 p-2 bg-gray-50 rounded border-l-2 border-blue-300">
                        <p className="text-sm text-gray-700 italic">"{citation.excerpt}"</p>
                      </div>
                    )}

                    <Link
                      to={`/output/${citation.source_output.id}`}
                      className="block p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition"
                    >
                      <div className="flex items-center space-x-2 mb-2">
                        <div className="w-6 h-6 bg-gray-300 rounded-full"></div>
                        <span className="text-sm font-medium text-gray-900">
                          {citation.source_output.author.display_name}
                        </span>
                        <span className="text-xs text-gray-500">
                          @{citation.source_output.author.username}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 line-clamp-2">
                        {citation.source_output.content}
                      </p>
                      <p className="text-xs text-blue-600 mt-2">View full output →</p>
                    </Link>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      )}

      {/* Hash Verification Modal */}
      {showVerificationModal && verificationResult && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-gray-900">Hash Verification Result</h3>
              <button
                onClick={() => setShowVerificationModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Overall Status */}
            <div className={`p-4 rounded-lg mb-4 ${
              verificationResult.content_hash_valid && verificationResult.full_hash_valid && verificationResult.hash_chain_valid
                ? 'bg-green-50 border border-green-200'
                : 'bg-red-50 border border-red-200'
            }`}>
              <p className={`text-sm font-medium ${
                verificationResult.content_hash_valid && verificationResult.full_hash_valid && verificationResult.hash_chain_valid
                  ? 'text-green-800'
                  : 'text-red-800'
              }`}>
                {verificationResult.message}
              </p>
            </div>

            {/* Detailed Checks */}
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Content Hash</span>
                <span className={`text-sm font-semibold ${
                  verificationResult.content_hash_valid ? 'text-green-600' : 'text-red-600'
                }`}>
                  {verificationResult.content_hash_valid ? '✓ Valid' : '✗ Invalid'}
                </span>
              </div>

              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Full Hash (Content + Metadata)</span>
                <span className={`text-sm font-semibold ${
                  verificationResult.full_hash_valid ? 'text-green-600' : 'text-red-600'
                }`}>
                  {verificationResult.full_hash_valid ? '✓ Valid' : '✗ Invalid'}
                </span>
              </div>

              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Hash Chain Integrity</span>
                <span className={`text-sm font-semibold ${
                  verificationResult.hash_chain_valid ? 'text-green-600' : 'text-red-600'
                }`}>
                  {verificationResult.hash_chain_valid ? '✓ Valid' : '✗ Invalid'}
                </span>
              </div>
            </div>

            {/* Info Box */}
            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h4 className="text-sm font-semibold text-blue-900 mb-2">What does this mean?</h4>
              <p className="text-xs text-blue-800">
                This verification proves the integrity of the content using cryptographic hashes.
                A valid result means the output has not been tampered with since creation.
                The hash chain ensures that all edit history is properly linked and immutable.
              </p>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setShowVerificationModal(false)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition text-sm font-medium"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
