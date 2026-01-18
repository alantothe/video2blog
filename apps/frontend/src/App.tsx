import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HomePage from './HomePage'
import ArticleTypesPage from './ArticleTypesPage'
import './styles.css'

const queryClient = new QueryClient()

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/article-types" element={<ArticleTypesPage />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
