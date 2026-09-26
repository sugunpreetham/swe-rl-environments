use task_03_rust_token_ast::{parse, Expr, Op, ParseError};

#[test]
fn test_tier1_operator_precedence() {
    let ast = parse("1 + 2 * 3").expect("Should parse");
    match ast {
        Expr::Binary { op: Op::Add, left, right } => {
            assert_eq!(*left, Expr::Number(1.0));
            match *right {
                Expr::Binary { op: Op::Mul, left: l2, right: r2 } => {
                    assert_eq!(*l2, Expr::Number(2.0));
                    assert_eq!(*r2, Expr::Number(3.0));
                }
                other => panic!("Expected multiplication on right, got {:?}", other),
            }
        }
        other => panic!("Expected addition at root, got {:?}", other),
    }
}

#[test]
fn test_tier1_parentheses_override() {
    let ast = parse("(1 + 2) * 3").expect("Should parse");
    match ast {
        Expr::Binary { op: Op::Mul, left, right } => {
            assert_eq!(*right, Expr::Number(3.0));
            match *left {
                Expr::Binary { op: Op::Add, left: l2, right: r2 } => {
                    assert_eq!(*l2, Expr::Number(1.0));
                    assert_eq!(*r2, Expr::Number(2.0));
                }
                other => panic!("Expected addition inside parens, got {:?}", other),
            }
        }
        other => panic!("Expected multiplication at root, got {:?}", other),
    }
}

#[test]
fn test_tier2_recursion_limit_guard() {
    // Construct 100 levels of nested parentheses
    let mut nested = String::new();
    for _ in 0..100 {
        nested.push('(');
    }
    nested.push_str("42");
    for _ in 0..100 {
        nested.push(')');
    }

    let result = parse(&nested);
    assert_eq!(result, Err(ParseError::RecursionLimitExceeded), 
        "Must return RecursionLimitExceeded rather than overflowing thread stack");
}

#[test]
fn test_tier3_unicode_identifier_support() {
    let ast = parse("alpha_1 + beta_2 * gamma_3").expect("Unicode and underscores must be valid identifiers");
    match ast {
        Expr::Binary { op: Op::Add, left, right } => {
            assert_eq!(*left, Expr::Ident("alpha_1".into()));
            match *right {
                Expr::Binary { op: Op::Mul, left: l2, right: r2 } => {
                    assert_eq!(*l2, Expr::Ident("beta_2".into()));
                    assert_eq!(*r2, Expr::Ident("gamma_3".into()));
                }
                _ => panic!("Expected multiplication"),
            }
        }
        _ => panic!("Expected addition"),
    }
}

#[test]
fn test_tier4_zero_panic_fuzzing() {
    // Malformed inputs that should error gracefully, never panic
    let fuzz_cases = [
        "(((",
        "1 + + 2",
        "**//",
        ")(",
        "12.34.56",
        "",
        "   ",
        "@#$%",
        "1 + 2 +",
    ];

    for case in &fuzz_cases {
        let res = parse(case);
        assert!(res.is_err(), "Malformed input '{}' must yield Err", case);
    }
}
