import { useState, useEffect } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import paymeApi from '../services/paymeApi';

export default function PaymentResult() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('loading');
  const [promoCode, setPromoCode] = useState(null);
  const [error, setError] = useState(null);
  useDocumentTitle(t('paymentResult.title'));

  useEffect(() => {
    const checkPaymentStatus = async () => {
      const transactionId = searchParams.get('transaction_id');
      const paymeStatus = searchParams.get('status');

      if (!transactionId) {
        if (paymeStatus === 'success') {
          setStatus('success');
          setPromoCode(searchParams.get('promo_code') || 'MAVU-PROMO');
        } else if (paymeStatus === 'cancelled' || paymeStatus === 'failed') {
          setStatus('failed');
          setError(t('paymentResult.cancelled'));
        } else {
          setStatus('failed');
          setError(t('paymentResult.invalidParams'));
        }
        return;
      }

      try {
        const response = await paymeApi.getTransactionStatus(transactionId);

        if (response.status === 'completed' || response.status === 'success') {
          setStatus('success');
          setPromoCode(response.promo_code || 'MAVU-' + Math.random().toString(36).substring(2, 8).toUpperCase());
        } else if (response.status === 'pending') {
          setStatus('pending');
        } else {
          setStatus('failed');
          setError(response.message || t('paymentResult.failed'));
        }
      } catch (err) {
        console.error('Status check error:', err);
        if (paymeStatus === 'success') {
          setStatus('success');
          setPromoCode(searchParams.get('promo_code') || 'MAVU-PROMO');
        } else {
          setStatus('failed');
          setError(t('paymentResult.checkError'));
        }
      }
    };

    checkPaymentStatus();
  }, [searchParams, t]);

  useEffect(() => {
    if (status === 'success' && promoCode) {
      navigate('/success', { state: { promoCode } });
    }
  }, [status, promoCode, navigate]);

  if (status === 'loading') {
    return (
      <section className="py-16 md:py-24 min-h-[80vh] flex items-center">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-lg text-center">
          <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-violet-500/20 flex items-center justify-center">
            <svg className="animate-spin w-8 h-8 text-violet-400" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-white mb-2">
            {t('paymentResult.checking')}
          </h1>
          <p className="text-sm text-gray-400">{t('paymentResult.pleaseWait')}</p>
        </div>
      </section>
    );
  }

  if (status === 'pending') {
    return (
      <section className="py-16 md:py-24 min-h-[80vh] flex items-center">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-lg text-center">
          <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-yellow-500/20 flex items-center justify-center">
            <svg className="w-8 h-8 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-white mb-2">
            {t('paymentResult.pending')}
          </h1>
          <p className="text-sm text-gray-400 mb-6">{t('paymentResult.pendingDesc')}</p>
          <Link
            to="/"
            className="inline-block px-6 py-3 rounded-full glass text-white text-sm font-semibold hover:bg-white/10 transition-all"
          >
            {t('paymentResult.backHome')}
          </Link>
        </div>
      </section>
    );
  }

  if (status === 'failed') {
    return (
      <section className="py-16 md:py-24 min-h-[80vh] flex items-center">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-lg text-center">
          <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-red-500/20 flex items-center justify-center">
            <svg className="w-8 h-8 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-white mb-2">
            {t('paymentResult.failedTitle')}
          </h1>
          <p className="text-sm text-gray-400 mb-6">{error || t('paymentResult.failedDesc')}</p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              to="/purchase"
              className="px-6 py-3 rounded-full bg-gradient-to-r from-violet-600 to-pink-600 text-white text-sm font-semibold hover:opacity-90 transition-all"
            >
              {t('paymentResult.tryAgain')}
            </Link>
            <Link
              to="/"
              className="px-6 py-3 rounded-full glass text-white text-sm font-semibold hover:bg-white/10 transition-all"
            >
              {t('paymentResult.backHome')}
            </Link>
          </div>
        </div>
      </section>
    );
  }

  return null;
}
