import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';

// Hero Section
function HeroSection() {
  const { t } = useTranslation();

  return (
    <section className="relative min-h-[80vh] md:min-h-[85vh] flex items-center justify-center pt-4 pb-12 md:pt-6 md:pb-16 overflow-hidden">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-6xl text-center">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-3 sm:px-4 py-1.5 sm:py-2 rounded-full glass mb-6 md:mb-8 animate-fade-in">
          <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
          <span className="text-xs sm:text-sm text-gray-300">{t('hero.badge')}</span>
        </div>

        {/* Title */}
        <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold mb-4 md:mb-6 animate-fade-in animation-delay-200">
          <span className="text-white">{t('hero.title1')}</span>
          <br />
          <span className="text-gradient">{t('hero.title2')}</span>
        </h1>

        {/* Description */}
        <p className="text-base sm:text-lg md:text-xl text-gray-400 max-w-xl md:max-w-2xl mx-auto mb-6 md:mb-8 animate-fade-in animation-delay-400 px-2">
          {t('hero.description')}{' '}
          <span className="text-violet-300">{t('hero.descriptionHighlight')}</span>{' '}
          {t('hero.descriptionEnd')}
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center mb-10 md:mb-16 animate-fade-in animation-delay-600 px-4 sm:px-0">
          <Link
            to="/purchase"
            className="px-6 sm:px-8 py-3 sm:py-4 rounded-full bg-gradient-to-r from-violet-600 to-pink-600 text-white font-semibold hover:opacity-90 transition-all duration-300 hover:shadow-lg hover:shadow-violet-500/30 hover:scale-105 text-sm sm:text-base"
          >
            {t('hero.buyPromo')}
          </Link>
          <a
            href="#features"
            className="px-6 sm:px-8 py-3 sm:py-4 rounded-full glass text-white font-semibold hover:bg-white/10 transition-all duration-300 text-sm sm:text-base"
          >
            {t('hero.learnMore')}
          </a>
        </div>

        {/* Stats */}
        <div className="flex flex-wrap justify-center gap-6 sm:gap-8 md:gap-12 lg:gap-16 animate-fade-in animation-delay-800">
          <div className="text-center min-w-[80px]">
            <div className="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-1">140+</div>
            <div className="text-xs sm:text-sm text-gray-400">{t('hero.stats.beta')}</div>
          </div>
          <div className="text-center min-w-[80px]">
            <div className="text-2xl sm:text-3xl md:text-4xl font-bold text-gradient">5-12</div>
            <div className="text-xs sm:text-sm text-gray-400">{t('hero.stats.age')}</div>
          </div>
          <div className="text-center min-w-[80px]">
            <div className="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-1">24/7</div>
            <div className="text-xs sm:text-sm text-gray-400">{t('hero.stats.always')}</div>
          </div>
        </div>
      </div>
    </section>
  );
}

// Features Section
function FeaturesSection() {
  const { t } = useTranslation();

  const features = [
    {
      key: 'listen',
      icon: (
        <svg className="w-6 h-6 sm:w-7 sm:h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
        </svg>
      ),
      gradient: 'from-violet-500 to-purple-600',
      bgGlow: 'bg-violet-500',
      shadowColor: 'shadow-violet-500/25',
    },
    {
      key: 'stories',
      icon: (
        <svg className="w-6 h-6 sm:w-7 sm:h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
      ),
      gradient: 'from-pink-500 to-rose-600',
      bgGlow: 'bg-pink-500',
      shadowColor: 'shadow-pink-500/25',
    },
    {
      key: 'recognize',
      icon: (
        <svg className="w-6 h-6 sm:w-7 sm:h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
        </svg>
      ),
      gradient: 'from-emerald-500 to-teal-600',
      bgGlow: 'bg-emerald-500',
      shadowColor: 'shadow-emerald-500/25',
    },
    {
      key: 'parents',
      icon: (
        <svg className="w-6 h-6 sm:w-7 sm:h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      ),
      gradient: 'from-amber-500 to-orange-600',
      bgGlow: 'bg-amber-500',
      shadowColor: 'shadow-amber-500/25',
    },
  ];

  return (
    <section id="features" className="py-10 md:py-12 relative">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 -left-32 w-64 h-64 bg-violet-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 -right-32 w-64 h-64 bg-pink-500/10 rounded-full blur-3xl" />
      </div>

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-6xl relative">
        {/* Header */}
        <div className="text-center mb-10 md:mb-12">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-strong mb-4">
            <div className="w-2 h-2 rounded-full bg-gradient-to-r from-violet-400 to-pink-400 animate-pulse" />
            <span className="text-xs sm:text-sm text-gray-300 font-medium">{t('features.badge')}</span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4">
            <span className="text-white">{t('features.title')}</span>
            <br />
            <span className="text-gradient">{t('features.titleHighlight')}</span>
          </h2>
          <p className="text-sm sm:text-base text-gray-400 max-w-xl md:max-w-2xl mx-auto">{t('features.description')}</p>
        </div>

        {/* Features Grid */}
        <div className="grid sm:grid-cols-2 gap-5 md:gap-8">
          {features.map((feature, index) => (
            <div
              key={feature.key}
              className="group relative"
            >
              {/* Card */}
              <div className={`relative h-full p-6 sm:p-8 rounded-3xl bg-white/[0.03] backdrop-blur-xl border border-white/10 transition-all duration-500 hover:border-white/20 hover:bg-white/[0.05] hover:shadow-2xl ${feature.shadowColor} overflow-hidden`}>

                {/* Animated gradient border on hover */}
                <div className="absolute inset-0 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500">
                  <div className={`absolute inset-[-1px] rounded-3xl bg-gradient-to-r ${feature.gradient} opacity-20`} />
                </div>

                {/* Background glow */}
                <div className={`absolute -top-24 -right-24 w-48 h-48 ${feature.bgGlow} rounded-full blur-[80px] opacity-0 group-hover:opacity-20 transition-opacity duration-700`} />

                {/* Decorative elements */}
                <div className="absolute top-4 right-4 flex gap-1.5">
                  <div className={`w-1.5 h-1.5 rounded-full ${feature.bgGlow} opacity-40 group-hover:opacity-80 transition-opacity`} />
                  <div className={`w-1.5 h-1.5 rounded-full ${feature.bgGlow} opacity-20 group-hover:opacity-60 transition-opacity delay-75`} />
                  <div className={`w-1.5 h-1.5 rounded-full ${feature.bgGlow} opacity-10 group-hover:opacity-40 transition-opacity delay-150`} />
                </div>

                {/* Content */}
                <div className="relative z-10">
                  {/* Icon */}
                  <div className="mb-5 sm:mb-6">
                    <div className={`relative inline-flex items-center justify-center w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-gradient-to-br ${feature.gradient} shadow-lg ${feature.shadowColor} transition-all duration-500 group-hover:scale-110 group-hover:rotate-3`}>
                      <div className="text-white">
                        {feature.icon}
                      </div>
                      {/* Icon shine effect */}
                      <div className="absolute inset-0 rounded-2xl bg-gradient-to-tr from-white/20 to-transparent" />
                    </div>
                  </div>

                  {/* Text */}
                  <h3 className="text-xl sm:text-2xl font-bold text-white mb-3 transition-all duration-300">
                    {t(`features.${feature.key}.title`)}
                  </h3>
                  <p className="text-sm sm:text-base text-gray-400 leading-relaxed group-hover:text-gray-300 transition-colors duration-300">
                    {t(`features.${feature.key}.description`)}
                  </p>
                </div>

                {/* Bottom gradient line */}
                <div className={`absolute bottom-0 left-6 right-6 h-px bg-gradient-to-r ${feature.gradient} opacity-0 group-hover:opacity-40 transition-opacity duration-500`} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// Screenshots Section
function ScreenshotsSection() {
  const { t } = useTranslation();

  return (
    <section id="screenshots" className="py-10 md:py-12 overflow-hidden">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-8 md:mb-12">
          <div className="inline-flex items-center gap-2 px-3 sm:px-4 py-1.5 sm:py-2 rounded-full glass mb-4">
            <span className="text-xs sm:text-sm text-gray-300">{t('screenshots.badge')}</span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-white mb-3">
            {t('screenshots.title')}
          </h2>
          <p className="text-sm sm:text-base text-gray-400 max-w-xl md:max-w-2xl mx-auto px-2">{t('screenshots.description')}</p>
        </div>

        {/* Phone Mockups */}
        <div className="flex flex-col sm:flex-row flex-wrap justify-center items-center gap-4 sm:gap-6 md:gap-8 mb-10 md:mb-12">
          {/* Phone 1 - Backgrounds */}
          <div className="phone-mockup w-48 sm:w-52 md:w-64 animate-float order-2 sm:order-1">
            <div className="phone-screen aspect-[9/19] overflow-hidden">
              <img
                src="/screenshots/app-main.png"
                alt={t('screenshots.backgrounds')}
                className="w-full h-full object-cover"
              />
            </div>
          </div>

          {/* Phone 2 - Main */}
          <div className="phone-mockup w-56 sm:w-60 md:w-72 sm:scale-105 md:scale-110 z-10 animate-float animation-delay-1000 order-1 sm:order-2">
            <div className="phone-screen aspect-[9/19] overflow-hidden">
              <img
                src="/screenshots/app-parents.png"
                alt={t('screenshots.main')}
                className="w-full h-full object-cover"
              />
            </div>
          </div>

          {/* Phone 3 - Customization */}
          <div className="phone-mockup w-48 sm:w-52 md:w-64 animate-float-reverse order-3">
            <div className="phone-screen aspect-[9/19] overflow-hidden">
              <img
                src="/screenshots/app-chat.png"
                alt={t('screenshots.customization')}
                className="w-full h-full object-cover"
              />
            </div>
          </div>
        </div>

        {/* Tags */}
        <div className="flex flex-wrap justify-center gap-2 sm:gap-3">
          {['ios', 'russian', 'voice', 'offline'].map((tag) => (
            <span
              key={tag}
              className="px-3 sm:px-4 py-1.5 sm:py-2 rounded-full glass text-xs sm:text-sm text-gray-300"
            >
              {t(`screenshots.tags.${tag}`)}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}

// Safety Section
function SafetySection() {
  const { t } = useTranslation();

  const steps = [
    {
      key: 'alarm',
      number: '01',
      icon: (
        <svg className="w-6 h-6 sm:w-7 sm:h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      ),
      gradient: 'from-red-500 to-orange-500',
      bgGlow: 'bg-red-500',
      shadowColor: 'shadow-red-500/20',
    },
    {
      key: 'calm',
      number: '02',
      icon: (
        <svg className="w-6 h-6 sm:w-7 sm:h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
        </svg>
      ),
      gradient: 'from-pink-500 to-rose-500',
      bgGlow: 'bg-pink-500',
      shadowColor: 'shadow-pink-500/20',
    },
    {
      key: 'notify',
      number: '03',
      icon: (
        <svg className="w-6 h-6 sm:w-7 sm:h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
      ),
      gradient: 'from-violet-500 to-purple-500',
      bgGlow: 'bg-violet-500',
      shadowColor: 'shadow-violet-500/20',
    },
  ];

  return (
    <section id="safety" className="py-10 md:py-12 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-gradient-to-b from-violet-500/5 to-transparent rounded-full blur-3xl" />
      </div>

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-6xl relative">
        {/* Header */}
        <div className="text-center mb-10 md:mb-12">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-strong mb-4">
            <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            <span className="text-xs sm:text-sm text-gray-300 font-medium">{t('safety.badge')}</span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4">
            <span className="text-white">{t('safety.title')}</span>{' '}
            <span className="text-gradient">{t('safety.titleHighlight')}</span>
          </h2>
          <p className="text-sm sm:text-base text-gray-400 max-w-xl md:max-w-2xl mx-auto">{t('safety.description')}</p>
        </div>

        {/* Steps - Timeline style */}
        <div className="relative max-w-4xl mx-auto mb-8 md:mb-10">
          {/* Timeline connector - desktop */}
          <div className="hidden sm:block absolute top-[60px] left-0 right-0 h-px">
            <div className="w-full h-full bg-gradient-to-r from-red-500/30 via-pink-500/30 to-violet-500/30" />
            <div className="absolute top-0 left-0 w-1/3 h-full bg-gradient-to-r from-transparent to-red-500/50 animate-pulse" style={{ animationDuration: '3s' }} />
          </div>

          <div className="grid sm:grid-cols-3 gap-6 md:gap-8">
            {steps.map((step, index) => (
              <div key={step.key} className="group relative">
                {/* Card */}
                <div className={`relative p-6 sm:p-7 rounded-3xl bg-white/[0.03] backdrop-blur-xl border border-white/10 transition-all duration-500 hover:border-white/20 hover:bg-white/[0.05] hover:shadow-2xl ${step.shadowColor} h-full`}>

                  {/* Background glow */}
                  <div className={`absolute -top-20 left-1/2 -translate-x-1/2 w-40 h-40 ${step.bgGlow} rounded-full blur-[80px] opacity-0 group-hover:opacity-15 transition-opacity duration-700`} />

                  {/* Step number - floating badge */}
                  <div className="absolute -top-3 left-6">
                    <div className={`px-3 py-1 rounded-full bg-gradient-to-r ${step.gradient} text-white text-xs font-bold shadow-lg ${step.shadowColor}`}>
                      {step.number}
                    </div>
                  </div>

                  {/* Content */}
                  <div className="relative z-10 pt-4">
                    {/* Icon */}
                    <div className="mb-5">
                      <div className={`relative inline-flex items-center justify-center w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-gradient-to-br ${step.gradient} shadow-lg ${step.shadowColor} transition-all duration-500 group-hover:scale-110`}>
                        <div className="text-white">
                          {step.icon}
                        </div>
                        <div className="absolute inset-0 rounded-2xl bg-gradient-to-tr from-white/20 to-transparent" />
                      </div>
                    </div>

                    {/* Text */}
                    <h3 className="text-lg sm:text-xl font-bold text-white mb-2">
                      {t(`safety.${step.key}.title`)}
                    </h3>
                    <p className="text-sm text-gray-400 leading-relaxed group-hover:text-gray-300 transition-colors duration-300">
                      {t(`safety.${step.key}.description`)}
                    </p>
                  </div>

                  {/* Decorative corner dots */}
                  <div className="absolute bottom-4 right-4 flex gap-1">
                    <div className={`w-1 h-1 rounded-full ${step.bgGlow} opacity-40`} />
                    <div className={`w-1 h-1 rounded-full ${step.bgGlow} opacity-20`} />
                  </div>
                </div>

                {/* Arrow connector - mobile */}
                {index < steps.length - 1 && (
                  <div className="sm:hidden flex justify-center py-3">
                    <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                    </svg>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Note */}
        <div className="relative max-w-3xl mx-auto">
          <div className="relative p-6 sm:p-8 rounded-3xl bg-gradient-to-br from-emerald-500/10 to-teal-500/5 border border-emerald-500/20 backdrop-blur-xl">
            {/* Icon */}
            <div className="absolute -top-4 left-6 sm:left-8">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center shadow-lg shadow-emerald-500/30">
                <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>

            <p className="text-sm sm:text-base text-gray-300 pt-2">
              <span className="text-emerald-400 font-semibold">{t('safety.important')}</span>{' '}
              {t('safety.note')}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

// Pricing Section
function PricingSection() {
  const { t } = useTranslation();

  const features = ['full', 'unlimited', 'parents', 'support'];

  return (
    <section id="pricing" className="py-10 md:py-12">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-8 md:mb-10">
          <div className="inline-flex items-center gap-2 px-3 sm:px-4 py-1.5 sm:py-2 rounded-full glass mb-4">
            <span className="text-xs sm:text-sm text-gray-300">{t('pricing.badge')}</span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-3">
            <span className="text-white">{t('pricing.title')}</span>{' '}
            <span className="text-gradient">{t('pricing.titleHighlight')}</span>
          </h2>
          <p className="text-sm sm:text-base text-gray-400">{t('pricing.description')}</p>
        </div>

        {/* Pricing Card */}
        <div className="max-w-sm sm:max-w-md mx-auto">
          <div className="glass-strong rounded-2xl sm:rounded-3xl p-6 sm:p-8 relative overflow-hidden group hover:scale-[1.02] transition-all duration-500 hover:shadow-2xl hover:shadow-violet-500/10">
            {/* Animated background effects */}
            <div className="absolute inset-0 bg-gradient-to-br from-violet-600/10 via-transparent to-pink-600/10 opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
            <div className="absolute -top-20 -right-20 w-40 h-40 bg-violet-500/20 rounded-full blur-3xl opacity-0 group-hover:opacity-60 transition-opacity duration-700" />
            <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-pink-500/20 rounded-full blur-3xl opacity-0 group-hover:opacity-60 transition-opacity duration-700" />

            {/* Shimmer effect */}
            <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
            </div>

            {/* Top gradient border */}
            <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-violet-500/50 to-transparent" />

            <div className="relative z-10">
              <p className="text-gray-400 text-xs sm:text-sm mb-2">{t('pricing.priceLabel')}</p>
              <div className="flex items-baseline gap-2 mb-1">
                <span className="text-4xl sm:text-5xl font-bold text-white">$11</span>
              </div>
              <p className="text-gray-500 text-xs sm:text-sm mb-6 sm:mb-8">{t('pricing.testPeriod')}</p>

              {/* Features */}
              <ul className="space-y-3 sm:space-y-4 mb-6 sm:mb-8">
                {features.map((feature, index) => (
                  <li
                    key={feature}
                    className="flex items-center gap-3 group/item transition-all duration-300 hover:translate-x-1"
                    style={{ animationDelay: `${index * 100}ms` }}
                  >
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-emerald-500/30 to-emerald-600/20 flex items-center justify-center flex-shrink-0 transition-all duration-300 group-hover/item:scale-110 group-hover/item:shadow-lg group-hover/item:shadow-emerald-500/20">
                      <svg className="w-3 h-3 text-emerald-400 group-hover/item:text-emerald-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <span className="text-sm sm:text-base text-gray-300 group-hover/item:text-white transition-colors duration-300">{t(`pricing.features.${feature}`)}</span>
                  </li>
                ))}
              </ul>

              {/* CTA */}
              <Link
                to="/purchase"
                className="block w-full py-3 sm:py-4 rounded-full bg-gradient-to-r from-violet-600 to-pink-600 text-white font-semibold text-center hover:opacity-90 transition-all duration-300 hover:shadow-lg hover:shadow-violet-500/30 text-sm sm:text-base"
              >
                {t('pricing.buyButton')}
              </Link>

              <p className="text-gray-500 text-[10px] sm:text-xs text-center mt-3 sm:mt-4">
                {t('pricing.comparison')}
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// CTA Section
function CTASection() {
  const { t } = useTranslation();

  return (
    <section className="py-10 md:py-12">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-6xl text-center">
        <div className="glass-strong rounded-2xl sm:rounded-3xl p-6 sm:p-8 md:p-10 relative overflow-hidden">
          {/* Background decoration */}
          <div className="absolute inset-0 bg-gradient-to-br from-violet-600/10 to-pink-600/10" />
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-1/2 h-px bg-gradient-to-r from-transparent via-violet-500 to-transparent" />

          <div className="relative">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-2">
              {t('cta.title')}
            </h2>
            <p className="text-lg sm:text-xl text-gradient font-medium mb-5 sm:mb-6">
              {t('cta.subtitle')}
            </p>
            <Link
              to="/purchase"
              className="inline-flex px-6 sm:px-8 py-3 sm:py-4 rounded-full bg-gradient-to-r from-violet-600 to-pink-600 text-white font-semibold hover:opacity-90 transition-all duration-300 hover:shadow-lg hover:shadow-violet-500/30 hover:scale-105 text-sm sm:text-base"
            >
              {t('cta.button')}
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}

// Main Home Component
export default function Home() {
  return (
    <>
      <HeroSection />
      <FeaturesSection />
      <ScreenshotsSection />
      <SafetySection />
      <PricingSection />
      <CTASection />
    </>
  );
}
