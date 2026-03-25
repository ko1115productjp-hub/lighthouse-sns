/**
 * Protocol Agreement Modal - Lighthouse of Intellect
 * Displays the protocol terms and requires explicit agreement before first post
 */

import { useState } from 'react';
import { api } from '../lib/api';

interface ProtocolAgreementModalProps {
  isOpen: boolean;
  onAgree: () => void;
  onCancel: () => void;
}

export function ProtocolAgreementModal({ isOpen, onAgree, onCancel }: ProtocolAgreementModalProps) {
  const [isAgreeing, setIsAgreeing] = useState(false);
  const [error, setError] = useState('');
  const [hasReadTerms, setHasReadTerms] = useState(false);

  if (!isOpen) return null;

  const handleAgree = async () => {
    if (!hasReadTerms) {
      setError('Please read the full protocol and check the box below');
      return;
    }

    setIsAgreeing(true);
    setError('');

    try {
      await api.post('/users/me/protocol-agreement');
      onAgree();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to record agreement');
    } finally {
      setIsAgreeing(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 bg-gradient-to-r from-blue-600 to-purple-600">
          <h2 className="text-2xl font-bold text-white mb-2">
            🏛️ Welcome to the Lighthouse of Intellect
          </h2>
          <p className="text-blue-100 text-sm">
            A permanent archive of human knowledge and thought
          </p>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto flex-1">
          <div className="prose max-w-none">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              Before you create your first public output, please understand:
            </h3>

            <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-4">
              <h4 className="font-semibold text-blue-900 mb-2">📌 Immutability & Permanence</h4>
              <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
                <li>
                  <strong>Public outputs cannot be deleted.</strong> Once published, they become part of the
                  permanent archive.
                </li>
                <li>
                  <strong>All edit history is preserved.</strong> Every change you make is recorded with
                  cryptographic hashing.
                </li>
                <li>
                  <strong>Your work survives you.</strong> Even if you leave the platform, your contributions
                  remain in the knowledge archive.
                </li>
              </ul>
            </div>

            <div className="bg-purple-50 border-l-4 border-purple-500 p-4 mb-4">
              <h4 className="font-semibold text-purple-900 mb-2">⚖️ From Personal to Collective</h4>
              <p className="text-sm text-purple-800 mb-2">
                By publishing public outputs, you agree that:
              </p>
              <ul className="text-sm text-purple-800 space-y-1 list-disc list-inside">
                <li>Your content transitions from <strong>personal property</strong> to <strong>shared human knowledge</strong>.</li>
                <li>Others can <strong>cite, critique, and build upon</strong> your work.</li>
                <li>Your ideas become part of the <strong>collective intellectual heritage</strong> of humanity.</li>
              </ul>
            </div>

            <div className="bg-green-50 border-l-4 border-green-500 p-4 mb-4">
              <h4 className="font-semibold text-green-900 mb-2">🔍 Objective Evaluation</h4>
              <ul className="text-sm text-green-800 space-y-1 list-disc list-inside">
                <li>Content is judged by <strong>originality and substance</strong>, not by who wrote it.</li>
                <li>Your follower count and reputation <strong>do not affect</strong> whether your work is valued.</li>
                <li>AI and community review focus on <strong>logical consistency</strong> and <strong>novelty</strong>.</li>
              </ul>
            </div>

            <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 mb-4">
              <h4 className="font-semibold text-yellow-900 mb-2">⚠️ Important Considerations</h4>
              <ul className="text-sm text-yellow-800 space-y-1 list-disc list-inside">
                <li>
                  <strong>Think before you publish.</strong> Public outputs are permanent and cannot be retracted.
                </li>
                <li>
                  <strong>Private outputs can be deleted,</strong> but public outputs become part of history.
                </li>
                <li>
                  <strong>You can edit public outputs,</strong> but all versions remain visible in the edit history.
                </li>
                <li>
                  <strong>Account deletion:</strong> You can anonymize your identity, but your public outputs remain.
                </li>
              </ul>
            </div>

            <div className="bg-gray-50 border border-gray-300 rounded-lg p-4 mb-4">
              <h4 className="font-semibold text-gray-900 mb-2">📜 License & Rights</h4>
              <p className="text-sm text-gray-700 mb-2">
                All public outputs are licensed under{' '}
                <a
                  href="https://creativecommons.org/licenses/by-sa/4.0/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-700 underline"
                >
                  CC BY-SA 4.0
                </a>
                , allowing others to:
              </p>
              <ul className="text-sm text-gray-700 space-y-1 list-disc list-inside">
                <li><strong>Share:</strong> Copy and redistribute your work</li>
                <li><strong>Adapt:</strong> Build upon and transform your work</li>
                <li><strong>Attribution:</strong> You receive credit for your contributions</li>
                <li><strong>ShareAlike:</strong> Derivatives must use the same license</li>
              </ul>
            </div>
          </div>

          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          {/* Acknowledgment Checkbox */}
          <div className="mt-6 p-4 bg-gray-100 rounded-lg">
            <label className="flex items-start space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={hasReadTerms}
                onChange={(e) => setHasReadTerms(e.target.checked)}
                className="mt-1 w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-900">
                I have read and understood the Lighthouse Protocol. I agree that my{' '}
                <strong>public outputs will be permanently stored</strong> and become part of the{' '}
                <strong>collective human knowledge archive</strong>. I accept that I cannot delete public
                outputs, though I can edit them (with full history preserved).
              </span>
            </label>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 bg-gray-50 flex justify-between items-center">
          <button
            onClick={onCancel}
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-100 transition"
          >
            Cancel
          </button>
          <button
            onClick={handleAgree}
            disabled={isAgreeing || !hasReadTerms}
            className="px-8 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-md hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition font-semibold flex items-center"
          >
            {isAgreeing ? (
              <>
                <svg
                  className="animate-spin -ml-1 mr-2 h-5 w-5 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                Agreeing...
              </>
            ) : (
              'I Agree - Join the Archive'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
