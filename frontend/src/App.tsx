import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Clients from './pages/Clients'
import ClientForm from './pages/ClientForm'
import Suppliers from './pages/Suppliers'
import SupplierForm from './pages/SupplierForm'
import Articles from './pages/Articles'
import ArticleForm from './pages/ArticleForm'
import Invoices from './pages/Invoices'
import InvoiceForm from './pages/InvoiceForm'
import InvoiceDetail from './pages/InvoiceDetail'
import Expenses from './pages/Expenses'
import ExpenseForm from './pages/ExpenseForm'
import Collaborators from './pages/Collaborators'
import CollaboratorForm from './pages/CollaboratorForm'
import Payroll from './pages/Payroll'
import Reports from './pages/Reports'
import Settings from './pages/Settings'
import Users from './pages/Users'
import UserForm from './pages/UserForm'
import Emails from './pages/Emails'
import EmailCompose from './pages/EmailCompose'
import EmailSettings from './pages/EmailSettings'
import Purchases from './pages/Purchases'
import PurchaseForm from './pages/PurchaseForm'
import Contracts from './pages/Contracts'
import ContractForm from './pages/ContractForm'
import FixedAssets from './pages/FixedAssets'
import Documents from './pages/Documents'
import Treasury from './pages/Treasury'
import Stock from './pages/Stock'
import Interventions from './pages/Interventions'
import InterventionForm from './pages/InterventionForm'
import Quotes from './pages/Quotes'
import QuoteForm from './pages/QuoteForm'
import CRM from './pages/CRM'
import OpportunityForm from './pages/OpportunityForm'
import AnnualAccounts from './pages/AnnualAccounts'
import Fiscal from './pages/Fiscal'
import Legal from './pages/Legal'
import Integrations from './pages/Integrations'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route
        path="/"
        element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }
      >
        <Route index element={<Dashboard />} />

        {/* Clients */}
        <Route path="clients" element={<Clients />} />
        <Route path="clients/new" element={<ClientForm />} />
        <Route path="clients/:id" element={<ClientForm />} />

        {/* Suppliers */}
        <Route path="suppliers" element={<Suppliers />} />
        <Route path="suppliers/new" element={<SupplierForm />} />
        <Route path="suppliers/:id" element={<SupplierForm />} />

        {/* Articles */}
        <Route path="articles" element={<Articles />} />
        <Route path="articles/new" element={<ArticleForm />} />
        <Route path="articles/:id" element={<ArticleForm />} />

        {/* Invoices */}
        <Route path="invoices" element={<Invoices />} />
        <Route path="invoices/new" element={<InvoiceForm />} />
        <Route path="invoices/:id" element={<InvoiceDetail />} />
        <Route path="invoices/:id/edit" element={<InvoiceForm />} />

        {/* Purchases */}
        <Route path="purchases" element={<Purchases />} />
        <Route path="purchases/new" element={<PurchaseForm />} />
        <Route path="purchases/:id" element={<PurchaseForm />} />
        <Route path="purchases/contracts" element={<Contracts />} />
        <Route path="purchases/contracts/new" element={<ContractForm />} />
        <Route path="purchases/contracts/:id" element={<ContractForm />} />
        <Route path="purchases/assets" element={<FixedAssets />} />
        <Route path="purchases/assets/new" element={<PurchaseForm />} />
        <Route path="purchases/assets/:id" element={<FixedAssets />} />

        {/* Expenses */}
        <Route path="expenses" element={<Expenses />} />
        <Route path="expenses/new" element={<ExpenseForm />} />
        <Route path="expenses/:id" element={<ExpenseForm />} />

        {/* Collaborators */}
        <Route path="collaborators" element={<Collaborators />} />
        <Route path="collaborators/new" element={<CollaboratorForm />} />
        <Route path="collaborators/:id" element={<CollaboratorForm />} />

        {/* Payroll */}
        <Route path="payroll" element={<Payroll />} />

        {/* Reports */}
        <Route path="reports" element={<Reports />} />

        {/* Settings */}
        <Route path="settings" element={<Settings />} />

        {/* Users */}
        <Route path="users" element={<Users />} />
        <Route path="users/new" element={<UserForm />} />
        <Route path="users/:id" element={<UserForm />} />

        {/* Emails */}
        <Route path="emails" element={<Emails />} />
        <Route path="emails/compose" element={<EmailCompose />} />
        <Route path="emails/settings" element={<EmailSettings />} />

        {/* Documents GED */}
        <Route path="documents" element={<Documents />} />

        {/* Treasury */}
        <Route path="treasury" element={<Treasury />} />

        {/* Stock */}
        <Route path="stock" element={<Stock />} />

        {/* Interventions */}
        <Route path="interventions" element={<Interventions />} />
        <Route path="interventions/new" element={<InterventionForm />} />
        <Route path="interventions/:id" element={<InterventionForm />} />

        {/* Quotes */}
        <Route path="quotes" element={<Quotes />} />
        <Route path="quotes/new" element={<QuoteForm />} />
        <Route path="quotes/:id" element={<QuoteForm />} />

        {/* CRM */}
        <Route path="crm" element={<CRM />} />
        <Route path="crm/opportunities/new" element={<OpportunityForm />} />
        <Route path="crm/opportunities/:id" element={<OpportunityForm />} />

        {/* Annual Accounts */}
        <Route path="annual-accounts" element={<AnnualAccounts />} />

        {/* Fiscal */}
        <Route path="fiscal" element={<Fiscal />} />

        {/* Legal */}
        <Route path="legal" element={<Legal />} />

        {/* Integrations */}
        <Route path="integrations" element={<Integrations />} />
      </Route>

      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
