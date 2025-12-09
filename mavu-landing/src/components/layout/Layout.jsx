import Header from './Header';
import Footer from './Footer';
import Background from '../ui/Background';

export default function Layout({ children }) {
  return (
    <div className="min-h-screen flex flex-col relative">
      <Background />
      <Header />
      <main className="flex-grow pt-20">{children}</main>
      <Footer />
    </div>
  );
}
