import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Home from './pages/Home';
import Privacy from './pages/Privacy';
import Offer from './pages/Offer';
import Contacts from './pages/Contacts';
import Purchase from './pages/Purchase';
import Success from './pages/Success';
import PaymentResult from './pages/PaymentResult';
import NotFound from './pages/NotFound';

import './i18n';

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/privacy" element={<Privacy />} />
          <Route path="/offer" element={<Offer />} />
          <Route path="/contacts" element={<Contacts />} />
          <Route path="/purchase" element={<Purchase />} />
          <Route path="/success" element={<Success />} />
          <Route path="/payment-result" element={<PaymentResult />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
