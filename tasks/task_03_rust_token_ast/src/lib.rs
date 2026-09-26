#[derive(Debug, PartialEq, Clone)]
pub enum Op {
    Add,
    Sub,
    Mul,
    Div,
}

#[derive(Debug, PartialEq, Clone)]
pub enum Expr {
    Number(f64),
    Ident(String),
    Binary {
        op: Op,
        left: Box<Expr>,
        right: Box<Expr>,
    },
}

#[derive(Debug, PartialEq, Clone)]
pub enum ParseError {
    UnexpectedToken(String),
    UnexpectedEof,
    InvalidNumber(String),
    RecursionLimitExceeded,
    TrailingTokens(String),
}

#[derive(Debug, PartialEq, Clone)]
pub(crate) enum Token {
    Number(f64),
    Ident(String),
    Plus,
    Minus,
    Star,
    Slash,
    LParen,
    RParen,
}

const MAX_RECURSION_DEPTH: usize = 64;

struct Lexer<'a> {
    _input: &'a str,
    indices: Vec<(usize, char)>,
    pos: usize,
}

impl<'a> Lexer<'a> {
    fn new(input: &'a str) -> Self {
        let indices: Vec<(usize, char)> = input.char_indices().collect();
        Self {
            _input: input,
            indices,
            pos: 0,
        }
    }

    fn peek(&self) -> Option<char> {
        self.indices.get(self.pos).map(|&(_, c)| c)
    }

    fn advance(&mut self) -> Option<char> {
        if self.pos < self.indices.len() {
            let ch = self.indices[self.pos].1;
            self.pos += 1;
            Some(ch)
        } else {
            None
        }
    }

    fn tokenize(&mut self) -> Result<Vec<Token>, ParseError> {
        let mut tokens = Vec::new();

        while let Some(ch) = self.peek() {
            if ch.is_whitespace() {
                self.advance();
                continue;
            }

            match ch {
                '+' => { self.advance(); tokens.push(Token::Plus); }
                '-' => { self.advance(); tokens.push(Token::Minus); }
                '*' => { self.advance(); tokens.push(Token::Star); }
                '/' => { self.advance(); tokens.push(Token::Slash); }
                '(' => { self.advance(); tokens.push(Token::LParen); }
                ')' => { self.advance(); tokens.push(Token::RParen); }
                '0'..='9' => {
                    let mut num_str = String::new();
                    let mut has_dot = false;
                    while let Some(c) = self.peek() {
                        if c.is_ascii_digit() {
                            num_str.push(c);
                            self.advance();
                        } else if c == '.' && !has_dot {
                            has_dot = true;
                            num_str.push(c);
                            self.advance();
                        } else {
                            break;
                        }
                    }
                    let val = num_str.parse::<f64>().map_err(|_| ParseError::InvalidNumber(num_str))?;
                    tokens.push(Token::Number(val));
                }
                c if c.is_alphabetic() || c == '_' => {
                    let mut id_str = String::new();
                    while let Some(c) = self.peek() {
                        if c.is_alphanumeric() || c == '_' {
                            id_str.push(c);
                            self.advance();
                        } else {
                            break;
                        }
                    }
                    tokens.push(Token::Ident(id_str));
                }
                other => {
                    return Err(ParseError::UnexpectedToken(other.to_string()));
                }
            }
        }

        Ok(tokens)
    }
}

pub struct Parser {
    tokens: Vec<Token>,
    pos: usize,
    depth: usize,
}

impl Parser {
    pub(crate) fn new(tokens: Vec<Token>) -> Self {
        Self {
            tokens,
            pos: 0,
            depth: 0,
        }
    }

    fn peek(&self) -> Option<&Token> {
        self.tokens.get(self.pos)
    }

    fn advance(&mut self) -> Option<Token> {
        if self.pos < self.tokens.len() {
            let tok = self.tokens[self.pos].clone();
            self.pos += 1;
            Some(tok)
        } else {
            None
        }
    }

    pub fn parse(&mut self) -> Result<Expr, ParseError> {
        if self.tokens.is_empty() {
            return Err(ParseError::UnexpectedEof);
        }
        let expr = self.parse_expr()?;
        if let Some(remaining) = self.peek() {
            return Err(ParseError::TrailingTokens(format!("{:?}", remaining)));
        }
        Ok(expr)
    }

    fn parse_expr(&mut self) -> Result<Expr, ParseError> {
        self.depth += 1;
        if self.depth > MAX_RECURSION_DEPTH {
            return Err(ParseError::RecursionLimitExceeded);
        }

        let mut left = self.parse_term()?;

        while let Some(tok) = self.peek() {
            let op = match tok {
                Token::Plus => Op::Add,
                Token::Minus => Op::Sub,
                _ => break,
            };
            self.advance();
            let right = self.parse_term()?;
            left = Expr::Binary {
                op,
                left: Box::new(left),
                right: Box::new(right),
            };
        }

        self.depth -= 1;
        Ok(left)
    }

    fn parse_term(&mut self) -> Result<Expr, ParseError> {
        let mut left = self.parse_factor()?;

        while let Some(tok) = self.peek() {
            let op = match tok {
                Token::Star => Op::Mul,
                Token::Slash => Op::Div,
                _ => break,
            };
            self.advance();
            let right = self.parse_factor()?;
            left = Expr::Binary {
                op,
                left: Box::new(left),
                right: Box::new(right),
            };
        }

        Ok(left)
    }

    fn parse_factor(&mut self) -> Result<Expr, ParseError> {
        match self.advance() {
            Some(Token::Number(n)) => Ok(Expr::Number(n)),
            Some(Token::Ident(id)) => Ok(Expr::Ident(id)),
            Some(Token::LParen) => {
                let inner = self.parse_expr()?;
                match self.advance() {
                    Some(Token::RParen) => Ok(inner),
                    _ => Err(ParseError::UnexpectedToken("Expected ')'".into())),
                }
            }
            Some(other) => Err(ParseError::UnexpectedToken(format!("{:?}", other))),
            None => Err(ParseError::UnexpectedEof),
        }
    }
}

pub fn parse(input: &str) -> Result<Expr, ParseError> {
    let mut lexer = Lexer::new(input);
    let tokens = lexer.tokenize()?;
    let mut parser = Parser::new(tokens);
    parser.parse()
}
