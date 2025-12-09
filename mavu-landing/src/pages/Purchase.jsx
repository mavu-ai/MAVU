import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import paymeApi from '../services/paymeApi';

export default function Purchase() {
  const { t } = useTranslation();
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  useDocumentTitle(t('purchase.title'));

  const handlePayment = async () => {
    setIsProcessing(true);
    setError(null);

    try {
      const response = await paymeApi.initPayment(1100);

      if (response.payment_url) {
        window.location.href = response.payment_url;
      } else {
        throw new Error('Payment URL not received');
      }
    } catch (err) {
      console.error('Payment error:', err);
      setError(t('purchase.error') || 'Payment initialization failed. Please try again.');
      setIsProcessing(false);
    }
  };

  return (
    <section className="py-16 md:py-24">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-md">
        {/* Header */}
        <div className="text-center mb-8 md:mb-12">
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-2">
            {t('purchase.title')}
          </h1>
          <p className="text-sm sm:text-base text-gray-400">{t('purchase.subtitle')}</p>
        </div>

        <div className="glass-strong rounded-2xl sm:rounded-3xl p-4 sm:p-6 md:p-8">
          {/* Payment Method - Payme only */}
          <div className="mb-6 md:mb-8">
            <p className="text-gray-400 text-xs sm:text-sm mb-3">{t('purchase.paymentMethod')}</p>
            <div className="flex items-center gap-3 p-4 rounded-xl border border-teal-500/30 bg-teal-500/10">
              {/* Payme Logo */}
              <div className="w-12 h-8 sm:w-14 sm:h-10 rounded-lg bg-[#00CCCC] flex items-center justify-center">
                <span className="text-white font-bold text-sm sm:text-base">Payme</span>
              </div>
              <div className="flex-1">
                <p className="text-sm sm:text-base text-white font-medium">{t('purchase.methods.payme')}</p>
                <p className="text-xs text-gray-400">{t('purchase.paymeDesc')}</p>
              </div>
              <div className="w-5 h-5 rounded-full bg-teal-500 flex items-center justify-center">
                <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>
          </div>

          {/* Order Summary */}
          <div className="glass rounded-xl sm:rounded-2xl p-3 sm:p-4 mb-4 sm:mb-6">
            <p className="text-gray-400 text-xs sm:text-sm mb-2 sm:mb-3">{t('purchase.orderSummary')}</p>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm sm:text-base text-white font-medium">{t('purchase.promo')}</p>
                <p className="text-xs sm:text-sm text-gray-500">{t('purchase.month')}</p>
              </div>
              <div className="text-right">
                <p className="text-xl sm:text-2xl font-bold text-white">$11</p>
              </div>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm text-center">
              {error}
            </div>
          )}

          {/* Pay Button */}
          <button
            onClick={handlePayment}
            disabled={isProcessing}
            className="w-full py-3 sm:py-4 rounded-xl bg-gradient-to-r from-violet-600 to-pink-600 text-white text-sm sm:text-base font-semibold hover:opacity-90 transition-all duration-300 hover:shadow-lg hover:shadow-violet-500/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isProcessing ? (
              <>
                <svg className="animate-spin w-4 h-4 sm:w-5 sm:h-5" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                {t('purchase.processing')}
              </>
            ) : (
              t('purchase.payButton')
            )}
          </button>

          {/* Security note */}
          <div className="flex items-center justify-center gap-2 mt-3 sm:mt-4 text-gray-500 text-xs sm:text-sm">
            <svg className="w-3.5 h-3.5 sm:w-4 sm:h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            {t('purchase.secure')}
          </div>

          {/* Agreement */}
          <p className="text-center text-gray-500 text-[10px] sm:text-xs mt-3 sm:mt-4">
            {t('purchase.agreement')}{' '}
            <Link to="/offer" className="text-violet-400 hover:underline">
              {t('purchase.offerLink')}
            </Link>
          </p>
        </div>
      </div>
    </section>
  );
}
